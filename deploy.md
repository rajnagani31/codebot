1. check EC2 is runing
2. check public ip is changed
3. check what ip your domain resolves to -> nerotechnology.online
4. Check the server's public IP -> sse into EC2 -> curl http://checkip.amazonaws.com
5. Verify Docker -> docker ps
6. verify frontend -> curl http://127.0.0.1:3001 or port 3000
7. verify backend -> curl http://127.0.0.1:8002 or 8000/docs
8. verify nginx -> sudo systemctl status nginx
9. Verify Nginx config -> sudo nginx -t -> they might be -> syntax is ok /n or test is successful
10. Reload Nginx (if you changed config) -> sudo systemctl reload nginx
11. Verify domain locally 
    - curl -I https://nerotechnology.online
    - curl -I https://nerotechnology.online
    - nslookup nerotechnology.online 8.8.8.8
    - 

12. How to prevent this problem

✅ Option 1 (Best): Use an Elastic IP

Right now:

EC2
↓

Stop instance

↓

Public IP changes

↓

DNS must be updated

what an elastic IP:
EC2
↓

Stop instance

↓

Start instance

↓

Same IP forever

✅ Option 2: Lower the TTL

yesterday our domain TTL(time to live) in hosteinger is 14400(4 hours) 
for development staging use: 300(5 minitus)

```python
# Public IP
curl http://checkip.amazonaws.com

# Docker
docker ps

# Nginx
sudo systemctl status nginx

# Nginx config
sudo nginx -t

# Listening 
sudo ss -ltnp

# Frontend
curl http://127.0.0.1:3001

# Backend
curl http://127.0.0.1:8002/docs

# Domain DNS (Google)
nslookup nerotechnology.online 8.8.8.8

# Domain DNS (Cloudflare)
nslookup nerotechnology.online 1.1.1.1
```