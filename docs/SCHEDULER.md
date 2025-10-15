Agendamento de sincronização DF-e

Objetivo: executar /api/dfe/sync periodicamente, respeitando a NT (pausa ~1h quando ultNSU==maxNSU).

Windows (Task Scheduler)

1. Abra o Agendador de Tarefas (taskschd.msc)
2. Ação: Criar Tarefa Básica -> Nome: DFe Sync Hourly
3. Disparador: Diariamente -> Repetir a tarefa a cada: 1 hora -> Duração: Indefinido
4. Ação: Iniciar um programa
   Programa/script:
   Powershell.exe
   Argumentos:
   -NoProfile -ExecutionPolicy Bypass -Command "Invoke-RestMethod -Method POST -Uri http://localhost:8001/api/dfe/sync?empresa_id=1 | Out-Null"
5. Marque "Executar com privilégios mais altos" se necessário.

WSL (cron)

1. Instale cron e habilite o serviço: sudo apt update && sudo apt install -y cron && sudo service cron start
2. Edite o crontab: crontab -e
3. Adicione a linha (executa a cada hora):
   0 \* \* \* \* curl -s -X POST "http://localhost:8001/api/dfe/sync?empresa_id=1" >/dev/null 2>&1

Linux puro (systemd timer)

1. Crie o service em ~/.config/systemd/user/dfe-sync.service:
   [Unit]
   Description=DF-e Sync

   [Service]
   WorkingDirectory=%h/openai-xml/dfe-sync
   Environment=PYTHONPATH=%h/openai-xml/dfe-sync
   ExecStart=%h/openai-xml/dfe-sync/.venv/bin/python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001
   Restart=on-failure

2. Crie o timer em ~/.config/systemd/user/dfe-sync.timer:
   [Unit]
   Description=Run DF-e Sync hourly

   [Timer]
   OnUnitActiveSec=1h
   Unit=dfe-sync.service

   [Install]
   WantedBy=default.target

3. Ative:
   systemctl --user daemon-reload
   systemctl --user enable --now dfe-sync.timer

Observação: Nenhuma instrução usa wsl.exe; são válidas em Linux/WSL nativamente.

Observações

- Ajuste a porta/URL conforme seu backend.
- Se usar autenticação, inclua cabeçalhos/credenciais no curl/Invoke-RestMethod.
- Para evitar consumo indevido (cStat 656), não reduza o intervalo mínimo.
- Se ultNSU==maxNSU, manter 1h é recomendado pela NT.
