Critérios de Classificação:

NF-e Entrada: CNPJ destinatário = empresa monitorada? Quando a nota for de entrada, validar o destinatario, que deve
ser um que esteja no cadastro de empresas monitoradas
NF-e Saída: CNPJ emissor = empresa monitorada? Quando a nota for de saída, validar o emissor, que deve um dos cnpjs monitorados
NF-e Terceiros: Nenhum CNPJ = empresa monitorada? Quando a nota é de entrada, no caso uma nota de terceiros, verificar quem é o destinatario e classificar. Podemos bolar já em contra-partida um cadastro de remententes. 
NF-e Transferência: Baseado em CFOP ou natureza operação? Notas de transferencia, para Depósito temporário. Tem alguns cfops que definem esse processo.
Tratamento de Duplicatas:

Como lidar com mesmo XML em múltiplos ZIPs? Validar pela chave da nfe, que deve ser unica. SE já estiver cadastrada na base, pular, ou comparar, e descartar. Apesar dos arquivos terem nomes diferentes, pode tratar do mesmo arquivo, precisa ser lido o cabeçalho antes de classificar.
Verificar por chave de acesso antes de processar? Sim, se já tiver importador, copiar para pasta, mas não duplicar o registro.
Performance:

Processar em lotes ou arquivo por arquivo? Pode processar por pasta, até um limite sem sobrecarregar ..... processe de 20 em 20 por exemplo, arquivos extraídos.
Paralelização para múltiplas empresas? Sim, temos mais de uma empresa monitorada, conforme o numero de certificado validos.
Monitoramento:

Dashboard web para acompanhar progresso? Sim, melhor, para contar, e contabilizar o que foi feito e o que não foi feito.
Logs detalhados de erros/sucessos? Sim, pode gravar logs com horarios, e tags de processo.