# Como atualizar a planilha de referência (colaboradores)

A referência do sistema é a **Planilha de colaboradores**, usada para listar departamentos, nomes dos colaboradores no filtro e para identificar quem lançou tempo. Ela deve ter as colunas:

- **IDs** – ID do usuário no Bitrix24  
- **Colaboradores** – Nome completo (com sobrenomes, se quiser)  
- **Departamentos** – Nome do departamento  

## Opção 1: Substituir o arquivo no projeto

1. Salve sua planilha atualizada (com sobrenomes, etc.) com o nome **Planilha de colaboradores.xlsx**.
2. Copie esse arquivo para a pasta do projeto (`bitrix-exporter`), substituindo o arquivo antigo.

O sistema passará a usar automaticamente essa planilha.

## Opção 2: Usar um caminho fixo (outra pasta)

Se a planilha estiver em outro lugar (por exemplo, na Área de Trabalho), defina a variável de ambiente **COLABORADORES_PLANILHA** com o caminho completo do arquivo.

Exemplo no `.env`:

```env
COLABORADORES_PLANILHA=C:\Users\Mateus\OneDrive\Área de Trabalho\Planilha de colaboradores.xlsx
```

Ou no terminal (PowerShell), antes de rodar o sistema:

```powershell
$env:COLABORADORES_PLANILHA = "C:\Users\Mateus\OneDrive\Área de Trabalho\Planilha de colaboradores.xlsx"
```

**Importante:** O arquivo da referência deve ter as colunas **IDs**, **Colaboradores** e **Departamentos**. Arquivos de exportação de tarefas (Exportacao_Tarefas_...) têm outro formato e não servem como planilha de colaboradores.
