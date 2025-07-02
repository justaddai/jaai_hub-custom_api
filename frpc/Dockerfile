FROM fatedier/frpc:v0.59.0

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY . .

ENTRYPOINT ["/entrypoint.sh"]