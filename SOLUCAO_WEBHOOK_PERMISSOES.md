# Solução: Adicionar Permissão para Lançamentos de Tempo

## Análise da Configuração Atual

Baseado na imagem da configuração do webhook, você tem as seguintes permissões:

✅ **Permissões Atuais:**
- `Tarefas (task)` - Permite buscar tarefas básicas
- `Tarefas (permissões estendidas) (tasks_extended)` - Permite operações avançadas
- `Listas (lists)`
- `Tarefas no celular (tasksmobile)`
- `Usuários (user)`
- `Campos personalizados de usuário (user.userfield)`
- `CRM (crm)`

❌ **Permissão Faltando:**
- Não há permissão específica para **lançamentos de tempo** (`tasks.elapseditem`)

---

## Solução: Adicionar Permissão

### Passo a Passo:

1. **Na tela de configuração do webhook que você mostrou:**

2. **Clique no botão "+ selecionar"** ao lado das permissões existentes

3. **Procure por uma das seguintes opções:**
   - `tasks.elapseditem` ou `Tarefas - Lançamentos de Tempo`
   - `tasks.elapsed` ou `Tarefas - Tempo Decorrido`
   - `Elapsed Items` ou `Lançamentos de Tempo`
   - Qualquer opção relacionada a "tempo", "elapsed", "time entries"

4. **Se não encontrar uma opção específica:**
   - Verifique se `Tarefas (permissões estendidas) (tasks_extended)` já deveria incluir isso
   - Pode ser necessário usar um webhook de administrador
   - Ou pode ser uma limitação da sua versão/plano do Bitrix24

5. **Adicione a permissão** e clique em **"SALVAR"**

6. **Atualize o arquivo `.env`** (se o token mudar):
   ```env
   BITRIX_WEBHOOK_BASE=https://consultoriaqs.bitrix24.com.br/rest/95/NOVO_TOKEN_SE_MUDAR/
   ```

7. **Reinicie o sistema** e teste novamente

---

## Alternativa: Verificar se tasks_extended já inclui

A permissão `Tarefas (permissões estendidas) (tasks_extended)` **deveria** incluir acesso a lançamentos de tempo, mas pode haver uma limitação específica.

### Teste Rápido:

1. Mantenha o webhook atual
2. Tente fazer uma requisição manual para verificar:
   ```
   https://consultoriaqs.bitrix24.com.br/rest/95/41pmjvmvglopvztq/tasks.task.elapseditem.get?taskId=25943
   ```
3. Se ainda retornar 404, a permissão `tasks_extended` não está incluindo lançamentos de tempo

---

## Possíveis Causas Adicionais

Se mesmo com as permissões corretas ainda não funcionar:

1. **Limitação do plano Bitrix24:**
   - Alguns planos podem não permitir acesso a lançamentos de tempo via REST API

2. **Configurações de segurança:**
   - O portal pode ter restrições específicas para esse tipo de dado

3. **Versão da API:**
   - Pode ser necessário usar um método diferente ou versão específica da API

---

## Solução Temporária Implementada

Enquanto isso não é resolvido, implementei uma **solução de fallback** que:

✅ Usa o campo `timeSpentInLogs` da tarefa (tempo total gasto)
✅ Mostra o tempo total na planilha
⚠️ Não mostra detalhes individuais (quem lançou, quando, comentários)

A tarefa 25943 que você mencionou deve aparecer na planilha com:
- **Tempo_Total_Gasto**: ~7,8 horas (28057 segundos)
- **Tempo_Lançamento**: ~7,8 horas
- **Quem_Lançou**: "Tempo total (detalhes não disponíveis)"
- **Comentário_Lançamento**: Explicação sobre a limitação

---

## Próximos Passos Recomendados

1. **Tente adicionar uma permissão específica** para lançamentos de tempo
2. **Se não encontrar**, verifique a documentação do Bitrix24 ou contate o suporte
3. **Teste novamente** após adicionar a permissão
4. **Use a solução de fallback** temporariamente se necessário
