# internet
[The Internet](https://twitter.com/SeanMcC1970/status/1500085009021124616?s=20&t=dbP3QpHZI3nL86EQt5lVxA), and how it's made.

# The Internet between 1990-1999
When IRC (try `dict IRC`) was hip. And people used mirc32 and some wrote, pressing "alt-f4" starts a hidden flightsimulator.

# DNS at that time
Yes you could simply get a zone transfer, dig them out and put them [here](dns), for the fun.
DNS was created 1983, before there was the hosts file, yes /etc/hosts.
CEO short summary, try `dict DNS` and read the RFC. The important RRs are SOA, NS, MX, and the whois database.

# Broken
- If you have MX records for a domain and you don't deliver mails to it, it is broken.
- If you have the choice of a TLD .edu or some country specific .xy the .edu one is better and should be used, anything else is poor decision.

# Why?
So why we create tools to setup your own DNS server? Map your network?
Because the given DNS servers are unreliable. Because there is no network documentation. Because...

# Really fast.
So where to start, how to get an overview? <TBD>. Once it works quite good and is fast, the plan is to also make appealing visualisations of it, and then have it via https://github.com/alexmyczko/ruptime

# A bit about security
"secure by default is only good for good press - that way clueless users get
'secure' install. It's the admin that makes system secure, not having closed everything
in base system - when you install debian and get only kernel+ash, it won't help anyone."
