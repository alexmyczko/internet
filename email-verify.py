#!/usr/bin/python
# -*- coding: utf-8 -*-
# Verify email addresses by contacting a domain's MX.
# Copyright (c) 2006 Göran Weinholt <goran@weinholt.se>
# DNS code based on the hostmx.py example from python-adns 1.0.0.

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

# Takes email addresses on stdin. Prints the email address back with
# either OK, SOFT, or FAIL and an explanation.

import adns, sys
import ADNS
import smtplib, socket
from string import join

# Ugly way to set a timeout on smtplib's sockets
oldsocket = socket.socket
def quicksocket(af, socktype, proto):
	s = oldsocket(af, socktype, proto)
	s.settimeout(20)
	return s
socket.socket = quicksocket

# Error while resolving the domain
class DnsError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return self.value

# Error while checking an email address
class CheckError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return self.value

# Temporary error while checking an email address
class CheckSoft(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return self.value

class QueryEngine(ADNS.QueryEngine):
    def submit_A(self, qname):
        from adns import rr

        if not hasattr(self, 'A_results'):
            self.A_results = {}
            self.PTR_results = {}
        self.A_results[qname] = ()
        self.submit(qname, rr.A, callback=self.A_callback)

    def A_callback(self, answer, qname, rr, flags, extra):
        if answer[0] in (adns.status.ok, adns.status.nodata,
                         adns.status.nxdomain):
            self.A_results[qname] = answer[3]
            for ip in self.A_results[qname]:
                if not self.PTR_results.has_key(ip):
                    self.submit_PTR(ip)
            
    def submit_PTR(self, qname):
        from adns import rr

        if not hasattr(self, 'PTR_results'):
            self.A_results = {}
            self.PTR_results = {}
        self.PTR_results[qname] = ()
        self.submit_reverse(qname, rr.PTRraw, callback=self.PTR_callback)

    def PTR_callback(self, answer, qname, rr, flags, extra):
        if answer[0] in (adns.status.ok, adns.status.nodata,
                         adns.status.nxdomain):
            self.PTR_results[qname] = answer[3]
            for name in self.PTR_results[qname]:
                if not self.A_results.has_key(name):
                    self.submit_A(name)
            
adns_state = adns.init(adns.iflags.noautosys)


def find_mx(hostname):
	global adns_state, DnsError

	s = QueryEngine(adns_state)
	r = s.synchronous(hostname, adns.rr.MXraw)

	found_mx = True
	try:
		adns.exception(r[0])
	except adns.NXDomain:
		raise DnsError("nonexistent domain")
	except adns.RemoteTempError:
		raise CheckSoft("temporary error resolving hostname")
	except adns.NoData:
		found_mx = False
	
	if r[1]: hostname = r[1]
	s.submit_A(hostname)

	for mx in r[3]: s.submit_A(mx[1])

	s.finish() # churn

	hosts = s.A_results

	# See RFC 2821 for how the resolving works.
	if found_mx:
		mxlist = []
		for pri,hostname in r[3]:
			for ip in hosts[hostname]:
				mxlist.append((pri, ip))
		return [ ip for (pri,ip) in mxlist ]
	else:
		if not hostname in hosts:
			raise DnsError("no MX or A records found")
		return list(hosts[hostname])

def check_one(email):
	if email.count('@') != 1:
		raise CheckError("address must contain exactly one @")
	hostname = email.split('@')[1]
	try:
		mxlist = find_mx(hostname)
	except DnsError, msg:
		raise CheckError("error resolving hostname: " + str(msg))

	# Contact the mail servers. The first server that answers should
	# also accept the address or we fail it. If no servers can be
	# contacted we fall through.
	for mx in mxlist:
		try:
			s = smtplib.SMTP(mx)
			if not (200 <= s.ehlo()[0] <= 299):
				(code,resp) = s.helo()
				if not (200 <= code <= 299):
					raise CheckError("our hostname not accepted: %s %s" %
									 (code,resp.replace('\n', ' ')))
			(code,resp) = s.mail('<>')
			if code != 250:
				s.quit()
				raise CheckError("our sender was not accepted: %s %s" %
								 (code,resp.replace('\n', ' ')))
			(code,resp) = s.rcpt(email)
			s.quit()
			if (400 <= code <= 499):
				raise CheckSoft("recipient may be accepted later: %s %s" %
								(code,resp.replace('\n', ' ')))
			elif not (200 <= code <= 299):
				raise CheckError("recipient was not accepted: %s %s" %
								 (code,resp.replace('\n', ' ')))
			else:
				print email, "OK", code, resp
				return
		except smtplib.SMTPException:
			continue
		except socket.error:
			continue

	raise CheckError("no mail server could be reached")
	
# Read email addresses from stdin and test each one.
while True:
	line = sys.stdin.readline()
	email = line.strip()
	if not line: break
	try:
		check_one(email)
	except CheckError, msg:
		print email, "FAIL", msg
		continue
	except CheckSoft, msg:
		print email, "SOFT", msg
		continue
	except:
		# Approve addresses where we had an internal error
		print email, "SOFT caused an internal ERROR"
		print >>sys.stderr, "internal error while verifying %s" % email
		continue
