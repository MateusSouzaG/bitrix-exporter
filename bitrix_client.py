"""Cliente HTTP para API REST do Bitrix24."""
import time
import logging
import json
from typing import Dict, List, Optional, Any
import requests
from config import BITRIX_WEBHOOK_BASE, BATCH_SIZE, MAX_RETRIES, RETRY_BACKOFF

logger = logging.getLogger(__name__)


class BitrixClient:
    """Cliente para interagir com a API REST do Bitrix24."""
    
    def __init__(self, webhook_base: str = None):
        """
        Inicializa o cliente Bitrix24.
        
        Args:
            webhook_base: URL base do webhook. Se None, usa BITRIX_WEBHOOK_BASE do config.
        """
        self.webhook_base = (webhook_base or BITRIX_WEBHOOK_BASE or "").strip()
        if not self.webhook_base:
            raise ValueError("Webhook base não configurado")
        
        # Garantir que termina com /
        if not self.webhook_base.endswith("/"):
            self.webhook_base += "/"
        # Log seguro para diagnóstico: mostra host e indica que token está configurado (sem expor o token)
        try:
            from urllib.parse import urlparse
            p = urlparse(self.webhook_base)
            mask = "***" if "/rest/" in self.webhook_base else "(configurado)"
            logger.info(f"Bitrix webhook em uso: {p.scheme}://{p.netloc}/rest/.../{mask}/")
        except Exception:
            logger.info("Bitrix webhook em uso: (configurado)")
    
    def _request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Faz uma requisição HTTP para a API Bitrix24 com retry automático.
        
        Args:
            method: Nome do método da API (ex: "tasks.task.list")
            params: Parâmetros da requisição
            
        Returns:
            Resposta da API como dicionário
            
        Raises:
            requests.RequestException: Em caso de erro HTTP após todas as tentativas
        """
        if params is None:
            params = {}
        
        url = f"{self.webhook_base}{method}"
        
        # Log detalhado para filtros de data
        if any("ACTIVITY_DATE" in str(k) for k in params.keys()):
            logger.info(f"Requisição para {method}")
            logger.info(f"  URL: {url}")
            logger.info(f"  Parâmetros: {params}")
            # Mostrar URL completa para debug
            from urllib.parse import urlencode
            full_url = f"{url}?{urlencode(params)}"
            logger.debug(f"  URL completa: {full_url[:200]}...")  # Limitar tamanho do log
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Verificar se a API retornou um erro
                if "error" in data:
                    error_msg = data.get("error_description", data.get("error", "Erro desconhecido"))
                    logger.warning(f"API retornou erro: {error_msg}")
                    raise ValueError(f"Erro da API Bitrix24: {error_msg}")
                
                return data
            
            except requests.Timeout:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_BACKOFF * (2 ** attempt)
                    logger.warning(f"Timeout na requisição. Tentativa {attempt + 1}/{MAX_RETRIES}. "
                                 f"Aguardando {wait_time}s antes de tentar novamente...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Timeout após {MAX_RETRIES} tentativas")
                    raise
            
            except requests.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_BACKOFF * (2 ** attempt)
                    logger.warning(f"Erro HTTP: {e}. Tentativa {attempt + 1}/{MAX_RETRIES}. "
                                 f"Aguardando {wait_time}s antes de tentar novamente...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Erro HTTP após {MAX_RETRIES} tentativas: {e}")
                    raise
    
    def _batch(self, commands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Executa múltiplos comandos em batch (até 50 por vez).
        
        Args:
            commands: Lista de comandos no formato [{"method": "...", "params": {...}}, ...]
            
        Returns:
            Lista de respostas na mesma ordem dos comandos
        """
        results = []
        
        # Processar em lotes de BATCH_SIZE
        for i in range(0, len(commands), BATCH_SIZE):
            batch = commands[i:i + BATCH_SIZE]
            
            # Formatar comandos para o formato batch do Bitrix24
            # O formato correto é: {"cmd": {"key1": "method?params", "key2": "method?params"}}
            # Onde key é um identificador único e o valor é a string do método com query params
            from urllib.parse import urlencode
            batch_cmd = {}
            cmd_keys = []
            
            for j, cmd in enumerate(batch):
                method = cmd["method"]
                params = cmd.get("params", {})
                # Criar chave única para o comando
                cmd_key = f"cmd_{i}_{j}"
                cmd_keys.append(cmd_key)
                # Formatar como string de query
                query_string = urlencode(params) if params else ""
                batch_cmd[cmd_key] = f"{method}?{query_string}" if query_string else method
            
            batch_url = f"{self.webhook_base}batch"
            
            try:
                # Bitrix24 batch usa POST
                # Log do que está sendo enviado
                logger.debug(f"Enviando batch: {json.dumps({'cmd': batch_cmd}, indent=2)[:500]}")
                
                response = requests.post(batch_url, json={"cmd": batch_cmd}, timeout=60)
                response.raise_for_status()
                data = response.json()
                
                # Log da resposta
                logger.debug(f"Resposta do batch: {json.dumps(data, indent=2)[:500]}")
                
                if "error" in data:
                    error_msg = data.get("error_description", data.get("error", "Erro desconhecido"))
                    logger.error(f"Erro no batch: {error_msg}")
                    # Continuar com resultados vazios para este batch
                    results.extend([None] * len(batch))
                else:
                    # Extrair resultados do formato batch
                    # A resposta vem como {"result": {"result": {"cmd_0_0": {...}, "cmd_0_1": {...}}}}
                    # Há um nível extra de "result" na resposta do batch
                    outer_result = data.get("result", {})
                    batch_result = outer_result.get("result", {})
                    
                    # Se não encontrou no nível interno, tentar no nível externo
                    if not batch_result:
                        batch_result = outer_result
                    
                    # Ordenar resultados pela ordem dos comandos
                    # Bitrix pode devolver cada resultado como string JSON; deserializar se for o caso
                    batch_results = []
                    for cmd_key in cmd_keys:
                        if cmd_key in batch_result:
                            val = batch_result[cmd_key]
                            if isinstance(val, str):
                                try:
                                    val = json.loads(val)
                                except (json.JSONDecodeError, TypeError):
                                    pass
                            batch_results.append(val)
                        else:
                            logger.warning(f"Chave {cmd_key} não encontrada na resposta do batch. Chaves disponíveis: {list(batch_result.keys())[:10]}")
                            batch_results.append(None)
                    results.extend(batch_results)
            
            except Exception as e:
                logger.error(f"Erro ao executar batch: {e}", exc_info=True)
                # Continuar com resultados vazios
                results.extend([None] * len(batch))
        
        return results
    
    def list_tasks(self, filters: Dict[str, Any] = None, start: int = 0) -> Dict[str, Any]:
        """
        Lista tarefas com paginação.
        
        Args:
            filters: Filtros para aplicar (ex: {"filter[RESPONSIBLE_ID]": 123})
            start: Índice de início para paginação
            
        Returns:
            Dicionário com "result" (lista de tarefas) e "total" (total de registros)
        """
        if filters is None:
            filters = {}
        
        params = {
            "start": start,
            **filters
        }
        
        # Log detalhado dos filtros sendo enviados (especialmente datas)
        if any("ACTIVITY_DATE" in str(k) for k in filters.keys()):
            logger.debug(f"Enviando filtros para tasks.task.list: {params}")
        
        response = self._request("tasks.task.list", params)
        
        # Log da resposta para debug
        if "ACTIVITY_DATE" in str(filters):
            total = response.get("total", 0)
            result = response.get("result", {})
            tasks_count = len(result.get("tasks", [])) if isinstance(result, dict) else len(result) if isinstance(result, list) else 0
            logger.debug(f"Resposta da API: total={total}, tasks retornadas={tasks_count}")
        
        return response
    
    def get_task(self, task_id: int) -> Dict[str, Any]:
        """
        Obtém detalhes de uma tarefa específica.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Dicionário com os detalhes da tarefa
        """
        params = {"taskId": task_id}
        response = self._request("tasks.task.get", params)
        return response.get("result", {}).get("task", {})
    
    def get_time_entries(self, task_id: int) -> List[Dict[str, Any]]:
        """
        Obtém lançamentos de tempo (elapsed items) de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            Lista de lançamentos de tempo
        """
        # IMPORTANTE:
        # Pelo comportamento observado e pela URL de exemplo fornecida por você,
        # o endpoint correto para buscar lançamentos é:
        #   task.elapseditem.getlist?TASKID=<id_da_tarefa>
        #
        # Ou seja:
        # - O método NÃO tem o prefixo "tasks." nem "tasks.task."
        # - O parâmetro usado é "TASKID" (maiúsculo), não "taskId"
        #
        # Exemplo real:
        #   .../task.elapseditem.getlist?TASKID=25943
        #
        # Por isso, ajustamos a chamada abaixo para refletir exatamente esse formato.
        params = {"TASKID": task_id}
        try:
            # Usar diretamente o método "task.elapseditem.getlist"
            response = self._request("task.elapseditem.getlist", params)

            # Estrutura esperada (mais comum):
            # {
            #   "result": [
            #       {"ID": "...", "TASK_ID": "...", "SECONDS": ..., ...},
            #       ...
            #   ]
            # }
            #
            # Mas, por segurança, tratamos também outros formatos possíveis.
            result = response.get("result", {})

            if isinstance(result, list):
                # Formato direto: lista de lançamentos
                return result
            elif isinstance(result, dict):
                # Alguns portais podem retornar dentro de "items" ou "elapsedItems"
                if "items" in result and isinstance(result["items"], list):
                    return result["items"]
                if "elapsedItems" in result and isinstance(result["elapsedItems"], list):
                    return result["elapsedItems"]
                # Caso venha em outro campo, registrar para depuração
                logger.warning(
                    f"Formato inesperado ao buscar lançamentos para tarefa {task_id}: chaves em result={list(result.keys())}"
                )
                # Tentar converter qualquer valor de lista encontrado
                for value in result.values():
                    if isinstance(value, list):
                        return value
                return []
            else:
                # Formato completamente inesperado
                logger.warning(
                    f"Resposta inesperada ao buscar lançamentos para tarefa {task_id}: tipo de result={type(result)}"
                )
                return []
        except Exception as e:
            logger.warning(f"Erro ao buscar lançamentos de tempo para tarefa {task_id}: {e}")
            return []
