# api-indices

é uma api que obtém alguns indicadores do banco central e da receita federal para 
a produção dos indíces de atualização e correção, bem como os juros que são
utilizados nos aplicativos de cálculos utilizados nos processos judiciais da AGU.

Todo mês a api busca no banco central os índices A, B e C e na página da receita
federal as taxas Selic, D e F.

Atualiza as tabelas de índices da AGU, bem como as tabelas com as taxas oficiais do 
banco central e da receita federal.

Provê os valores dos índices por período ou por data focal.
