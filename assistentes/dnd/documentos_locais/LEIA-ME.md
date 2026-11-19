# Documentos locais (ficam só no seu computador)

Coloque aqui o que é seu e não pode ir para o GitHub:

- o seu livro de regras em PDF (ex.: o Livro do Jogador que você comprou);
- anotações da sua campanha em `.md` (use títulos `## ` para separar os assuntos) ou `.txt`.

O Git ignora tudo nesta pasta, menos este arquivo. Só o modo de conversa
(`python -m motor.conversar --assistente dnd`) lê estes documentos; a avaliação
automática usa apenas os documentos públicos do repositório.

Para ler PDF, instale uma vez: `pip install pypdf`. Na primeira conversa o livro é
lido e guardado num cache (pode levar um minuto); nas próximas, abre rápido.
