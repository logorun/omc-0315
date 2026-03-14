# Gateway Agent Troubleshooting Guide

## Issue: Gateway Agent provision_failed on 216.116.160.79 (电商AI Gateway)

### Agent Details
- **Agent ID**: 
- **Gateway ID**: 
- **Gateway URL**: 
- **Server**: 216.116.160.79 (ecs95033)

### Root Cause Analysis

1. **Gateway Process Instability**: The OpenClaw gateway process was receiving frequent SIGTERM signals causing it to restart every 10-60 seconds.

2. **Systemd Service Configuration**: The systemd user service  had  which combined with the SIGTERM signals created a restart loop.

3. **Caddy Reverse Proxy Timing**: When the gateway restarted, Caddy would get HTTP 502 errors trying to connect to the gateway.

4. **Missing Device Pairing**: The MC backend device needed to be paired with the gateway.

### Solution Steps

#### 1. Disable Auto-Restart in OpenClaw Config


#### 2. Update Systemd Service to Use Restart=on-failure


#### 3. Pair Device with Gateway


#### 4. Update Agent Status in MC Database


#### 5. Reload Caddy


### Verification Commands

● openclaw-gateway.service - OpenClaw Gateway (v2026.3.11)
     Loaded: loaded (/root/.config/systemd/user/openclaw-gateway.service; enabled; preset: enabled)
     Active: active (running) since Fri 2026-03-13 06:19:18 CST; 9h ago
 Invocation: ba59b80303a84e18819112d4c02822b3
   Main PID: 1410141 (openclaw-gatewa)
      Tasks: 337 (limit: 9520)
     Memory: 2.4G (peak: 4G)
        CPU: 9h 16min 59.369s
     CGroup: /user.slice/user-0.slice/user@0.service/app.slice/openclaw-gateway.service
             ├─ 116056 node dist/cli.js start
             ├─ 116619 node dist/cli.js start
             ├─ 116673 node dist/cli.js start
             ├─ 116776 node dist/cli.js start
             ├─ 117041 node dist/cli.js start
             ├─ 117407 node dist/cli.js start
             ├─ 117428 /usr/lib/node_modules/opencode-ai/bin/.opencode serve
             ├─ 117479 node dist/cli.js start
             ├─ 117667 node dist/cli.js start
             ├─ 745727 /usr/bin/node /usr/bin/mcporter daemon start --foreground
             ├─ 746051 /usr/bin/node /usr/bin/mcporter daemon start --foreground
             ├─ 746297 /usr/bin/node /usr/bin/mcporter daemon start --foreground
             ├─ 746561 /usr/bin/node /usr/bin/mcporter daemon start --foreground
             ├─ 746790 /usr/bin/node /usr/bin/mcporter daemon start --foreground
             ├─ 747024 /usr/bin/node /usr/bin/mcporter daemon start --foreground
             ├─ 747288 /usr/bin/node /usr/bin/mcporter daemon start --foreground
             ├─ 748406 /usr/bin/node /usr/bin/mcporter daemon start --foreground
             ├─ 750372 /usr/bin/node /usr/bin/mcporter daemon start --foreground
             ├─ 750751 /usr/bin/node /usr/bin/mcporter daemon start --foreground
             ├─ 750986 /usr/bin/node /usr/bin/mcporter daemon start --foreground
             ├─ 909680 /usr/lib/node_modules/opencode-ai/bin/.opencode run /root/.local/share/opencode/bin/node_modules/yaml-language-server/out/server/src/server.js --stdio
             ├─ 910590 /usr/lib/node_modules/opencode-ai/bin/.opencode run /root/.local/share/opencode/bin/node_modules/pyright/dist/pyright-langserver.js --stdio
             ├─1006898 cat
             ├─1006901 /opt/google/chrome/chrome_crashpad_handler --monitor-self --monitor-self-annotation=ptype=crashpad-handler "--database=/root/.config/google-chrome/Crash Reports" --url=https://clients2.google.com/cr/report --annotation=channel= "--annotation=lsb-release=Debian GNU/Linux 13 (trixie)" --annotation=plat=Linux --annotation=prod=Chrome_Linux --annotation=ver=145.0.7632.159 --initial-client-fd=5 --shared-client-connection
             ├─1006903 /opt/google/chrome/chrome_crashpad_handler --no-periodic-tasks --monitor-self-annotation=ptype=crashpad-handler "--database=/root/.config/google-chrome/Crash Reports" --url=https://clients2.google.com/cr/report --annotation=channel= "--annotation=lsb-release=Debian GNU/Linux 13 (trixie)" --annotation=plat=Linux --annotation=prod=Chrome_Linux --annotation=ver=145.0.7632.159 --initial-client-fd=4 --shared-client-connection
             ├─1006908 "/opt/google/chrome/chrome --type=zygote --no-zygote-sandbox --no-sandbox --headless=new --crashpad-handler-pid=1006901 --enable-crash-reporter=, --noerrdialogs --user-data-dir=/root/.openclaw/browser/openclaw/user-data --change-stack-guard-on-fork=enable --no-first-run --ozone-platform=headless --ozone-override-screen-size=800,600 --use-angle=swiftshader-webgl"
             ├─1006909 "/opt/google/chrome/chrome --type=zygote --no-sandbox --headless=new --crashpad-handler-pid=1006901 --enable-crash-reporter=, --noerrdialogs --user-data-dir=/root/.openclaw/browser/openclaw/user-data --change-stack-guard-on-fork=enable --no-first-run --ozone-platform=headless --ozone-override-screen-size=800,600 --use-angle=swiftshader-webgl"
             ├─1006928 "/opt/google/chrome/chrome --type=gpu-process --no-sandbox --disable-dev-shm-usage --headless=new --ozone-platform=headless --use-angle=swiftshader-webgl --crashpad-handler-pid=1006901 --enable-crash-reporter=, --noerrdialogs --user-data-dir=/root/.openclaw/browser/openclaw/user-data --change-stack-guard-on-fork=enable --gpu-preferences=UAAAAAAAAAAgAQAEAAAAAAAAAAAAAGAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAAAAAAAYAAAAAAAAABgAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAgAAAAAAAAA --use-gl=disabled --shared-files --field-trial-handle=3,i,16945135290225870074,6579515928711523115,262144 --disable-features=MediaRouter,PaintHolding,Translate --variations-seed-version --trace-process-track-uuid=3190708988185955192"
             ├─1006930 "/opt/google/chrome/chrome --type=utility --utility-sub-type=network.mojom.NetworkService --lang=en-US --service-sandbox-type=none --no-sandbox --disable-dev-shm-usage --use-angle=swiftshader-webgl --crashpad-handler-pid=1006901 --enable-crash-reporter=, --noerrdialogs --user-data-dir=/root/.openclaw/browser/openclaw/user-data --change-stack-guard-on-fork=enable --shared-files=v8_context_snapshot_data:100 --field-trial-handle=3,i,16945135290225870074,6579515928711523115,262144 --disable-features=MediaRouter,PaintHolding,Translate --variations-seed-version --trace-process-track-uuid=3190708989122997041"
             ├─1006936 "/opt/google/chrome/chrome --type=utility --utility-sub-type=storage.mojom.StorageService --lang=en-US --service-sandbox-type=utility --no-sandbox --disable-dev-shm-usage --use-angle=swiftshader-webgl --crashpad-handler-pid=1006901 --enable-crash-reporter=, --noerrdialogs --user-data-dir=/root/.openclaw/browser/openclaw/user-data --change-stack-guard-on-fork=enable --shared-files=v8_context_snapshot_data:100 --field-trial-handle=3,i,16945135290225870074,6579515928711523115,262144 --disable-features=MediaRouter,PaintHolding,Translate --variations-seed-version --trace-process-track-uuid=3190708990060038890"
             ├─1006957 "/opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=1006901 --enable-crash-reporter=, --noerrdialogs --user-data-dir=/root/.openclaw/browser/openclaw/user-data --change-stack-guard-on-fork=enable --no-sandbox --disable-dev-shm-usage --remote-debugging-port=18800 --ozone-platform=headless --disable-gpu-compositing --disable-blink-features=AutomationControlled --lang=en-US --num-raster-threads=4 --enable-main-frame-before-activation --renderer-client-id=6 --time-ticks-at-unix-epoch=-1772905598547292 --launch-time-ticks=323368973438 --shared-files=v8_context_snapshot_data:100 --field-trial-handle=3,i,16945135290225870074,6579515928711523115,262144 --disable-features=MediaRouter,PaintHolding,Translate --variations-seed-version --trace-process-track-uuid=3190708991934122588"
             ├─1006958 "/opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=1006901 --enable-crash-reporter=, --noerrdialogs --user-data-dir=/root/.openclaw/browser/openclaw/user-data --change-stack-guard-on-fork=enable --no-sandbox --disable-dev-shm-usage --remote-debugging-port=18800 --ozone-platform=headless --disable-gpu-compositing --disable-blink-features=AutomationControlled --lang=en-US --num-raster-threads=4 --enable-main-frame-before-activation --renderer-client-id=5 --time-ticks-at-unix-epoch=-1772905598547292 --launch-time-ticks=323368975439 --shared-files=v8_context_snapshot_data:100 --field-trial-handle=3,i,16945135290225870074,6579515928711523115,262144 --disable-features=MediaRouter,PaintHolding,Translate --variations-seed-version --trace-process-track-uuid=3190708990997080739"
             ├─1006980 "/opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=1006901 --enable-crash-reporter=, --noerrdialogs --user-data-dir=/root/.openclaw/browser/openclaw/user-data --change-stack-guard-on-fork=enable --no-sandbox --disable-dev-shm-usage --remote-debugging-port=18800 --ozone-platform=headless --disable-gpu-compositing --disable-blink-features=AutomationControlled --lang=en-US --num-raster-threads=4 --enable-main-frame-before-activation --renderer-client-id=7 --time-ticks-at-unix-epoch=-1772905598547292 --launch-time-ticks=323374795391 --shared-files=v8_context_snapshot_data:100 --field-trial-handle=3,i,16945135290225870074,6579515928711523115,262144 --disable-features=MediaRouter,PaintHolding,Translate --variations-seed-version --trace-process-track-uuid=3190708992871164437"
             ├─1016465 "/opt/google/chrome/chrome --type=renderer --crashpad-handler-pid=1006901 --enable-crash-reporter=, --noerrdialogs --user-data-dir=/root/.openclaw/browser/openclaw/user-data --change-stack-guard-on-fork=enable --no-sandbox --disable-dev-shm-usage --remote-debugging-port=18800 --ozone-platform=headless --disable-gpu-compositing --disable-blink-features=AutomationControlled --lang=en-US --num-raster-threads=4 --enable-main-frame-before-activation --renderer-client-id=8 --time-ticks-at-unix-epoch=-1772905598547292 --launch-time-ticks=337769128230 --shared-files=v8_context_snapshot_data:100 --field-trial-handle=3,i,16945135290225870074,6579515928711523115,262144 --disable-features=MediaRouter,PaintHolding,Translate --variations-seed-version --trace-process-track-uuid=3190708993808206286"
             └─1410141 openclaw-gateway

Mar 13 15:34:15 ECS94722 node[1410141]: 2026-03-13T07:34:15.768Z [telegram] autoSelectFamily=false (config)
Mar 13 15:34:15 ECS94722 node[1410141]: 2026-03-13T07:34:15.772Z [telegram] fetch fallback: forcing autoSelectFamily=false + dnsResultOrder=ipv4first
Mar 13 15:39:06 ECS94722 node[1410141]: 2026-03-13T07:39:06.080Z [plugins] [hooks] before_prompt_build handler from self-evolve failed: Error: 502 status code (no body)
Mar 13 15:49:05 ECS94722 node[1410141]: 2026-03-13T07:49:05.223Z [plugins] [hooks] before_prompt_build handler from self-evolve failed: Error: 502 status code (no body)
Mar 13 15:58:22 ECS94722 node[1410141]: 2026-03-13T07:58:22.583Z [plugins] [hooks] before_prompt_build handler from self-evolve failed: Error: 502 status code (no body)
Mar 13 15:59:34 ECS94722 node[1410141]: 2026-03-13T07:59:34.198Z [health-monitor] [telegram:default] health-monitor: restarting (reason: stale-socket)
Mar 13 15:59:35 ECS94722 node[1410141]: 2026-03-13T07:59:35.194Z [telegram] [default] starting provider (@logos_worker2bot)
Mar 13 15:59:35 ECS94722 node[1410141]: 2026-03-13T07:59:35.198Z [telegram] autoSelectFamily=true (default-node22)
Mar 13 16:09:02 ECS94722 node[1410141]: 2026-03-13T08:09:02.646Z [plugins] [hooks] before_prompt_build handler from self-evolve failed: Error: 502 status code (no body)
Mar 13 16:15:56 ECS94722 node[1410141]: 2026-03-13T08:15:56.186Z [reload] config change detected; evaluating reload (commands.restart)
Mar 13 16:15:56 ECS94722 node[1410141]: 2026-03-13T08:15:56.194Z [reload] config change requires gateway restart (commands.restart) — deferring until 2 operation(s), 1 embedded run(s) complete
{"connected":false,"gateway_url":"wss://gw-79-ec.imlogo.net:443","sessions_count":null,"sessions":null,"main_session":null,"main_session_error":null,"error":"server rejected WebSocket connection: HTTP 502"}

### Key Learnings

1. **Avoid Restart=always**: Using  is more stable for gateway services that may receive external signals.

2. **Disable commands.restart**: Setting  in openclaw.json prevents the gateway from self-restarting.

3. **Device Pairing Required**: MC backend requires explicit device pairing before it can connect to the gateway.

4. **Database Status Updates**: Sometimes manual database updates are needed to fix stuck provisioning states.

### Future Improvements

1. Add health check endpoint to MC API for gateway status
2. Implement automatic device pairing in MC provisioning flow
3. Add systemd watchdog support for better crash detection
4. Create monitoring alerts for gateway restart frequency
