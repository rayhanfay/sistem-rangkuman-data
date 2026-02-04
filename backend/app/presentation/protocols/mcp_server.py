import traceback
import json
import asyncio
import logging
from datetime import datetime
from dataclasses import is_dataclass, asdict
from enum import Enum
from typing import Dict, Any, List, Optional
from fastapi import WebSocket

from app.dependencies import AppContainer, get_user_repository
from app.presentation.schemas import AnalysisOptions, UserRole
from app.infrastructure.database.database import SessionLocal
from app.presentation.auth import get_current_user_from_token

class McpServer:
    """
    Implementasi McpServer sesuai standar Model Context Protocol (MCP).
    Mendukung eksekusi tool, resource, dan notifikasi progres real-time.
    """
    def __init__(self):
        self.container = AppContainer()
        self.protocol_version = "2024-11-05"
        self.server_info = {
            "name": "PHR Asset Management Server",
            "version": "8.1.0"
        }
        self.capabilities = {
            "tools": {"listChanged": False},
            "resources": {"listChanged": True, "subscribe": False},
            "prompts": {"listChanged": False}
        }
        
        self.errors = {
            "PARSE_ERROR": -32700, 
            "INVALID_REQUEST": -32600,
            "METHOD_NOT_FOUND": -32601, 
            "INVALID_PARAMS": -32602,
            "INTERNAL_ERROR": -32603, 
            "RESOURCE_NOT_FOUND": -32001,
            "TOOL_EXECUTION_FAILED": -32002, 
            "DATABASE_CONNECTION_FAILED": -32005,
        }

    async def handle_request(self, request: dict, websocket: WebSocket) -> Optional[dict]:
        """Entry point untuk semua request JSON-RPC yang masuk via WebSocket."""
        if not isinstance(request, dict):
            return self._create_error_response(None, self.errors["PARSE_ERROR"], "Request must be a JSON object")
        
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if not method:
            return self._create_error_response(request_id, self.errors["INVALID_REQUEST"], "Method is required")
        
        response = {"jsonrpc": "2.0", "id": request_id}
        db_session = None
        
        try:
            db_session = SessionLocal()
            
            handler_map = {
                "initialize": self._handle_initialize,
                "notifications/initialized": lambda p, d, w: {},
                "tools/list": self._handle_tools_list,
                "tools/call": self._handle_tools_call,
                "resources/list": self._handle_resources_list,
                "resources/read": self._handle_resources_read,
                "prompts/list": self._handle_prompts_list,
                "prompts/get": self._handle_prompts_get,
            }

            handler = handler_map.get(method)
            if handler:
                result = await handler(params, db_session, websocket)
                if result is not None:
                    response["result"] = result
                else:
                    return None
            else:
                response["error"] = self._create_error_structure(
                    self.errors["METHOD_NOT_FOUND"], f"Method '{method}' not found"
                )
                
        except ValueError as e:
            logging.error(f"[MCP] Validation error: {e}")
            response["error"] = self._create_error_structure(self.errors["INVALID_PARAMS"], str(e))
        except Exception as e:
            logging.error(f"[MCP] Internal error: {e}")
            traceback.print_exc()
            response["error"] = self._create_error_structure(self.errors["INTERNAL_ERROR"], f"Server error: {e}")
        finally:
            if db_session:
                db_session.close()
            
        return response

    def _create_error_structure(self, code: int, message: str, data: dict = None) -> dict:
        error_obj = {"code": code, "message": message}
        if data: 
            error_obj["data"] = data
        return error_obj

    def _create_error_response(self, request_id: Optional[str], code: int, message: str, data: dict = None) -> dict:
        return {"jsonrpc": "2.0", "id": request_id, "error": self._create_error_structure(code, message, data)}
    
    def _get_tool_schemas(self) -> dict:
        """
        Definisi skema input untuk LLM. 
        PENTING: Deskripsi di sini menentukan seberapa akurat LLM memanggil tool.
        """
        return {
            "get_dashboard_data": {
                "properties": {
                    "area": {"type": "string"}
                }
            },
            "trigger_analysis": {
                "properties": {
                    "sheet_name": {"type": "string", "default": "MasterDataAsset"},
                    "data_overview": {"type": "boolean"},
                    "summarize": {"type": "boolean"},
                    "insight": {"type": "boolean"},
                    "check_duplicates": {"type": "boolean"},
                    "financial_analysis": {"type": "boolean"}
                }
            },
            "create_user": {
                "properties": {
                    "email": {"type": "string"},
                    "password": {"type": "string"},
                    "role": {"type": "string", "enum": ["admin", "user"]}
                },
                "required": ["email", "password", "role"]
            },
            "delete_user": {
                "properties": {
                    "user_id": {"type": "integer"}
                },
                "required": ["user_id"]
            },
            "update_user_email": {
                "properties": {
                    "user_id": {"type": "integer"},
                    "new_email": {"type": "string"}
                },
                "required": ["user_id", "new_email"]
            },
            "update_user_role": {
                "properties": {
                    "user_id": {"type": "integer"},
                    "new_role": {"type": "string", "enum": ["admin", "user"]}
                },
                "required": ["user_id", "new_role"]
            },
            "save_analysis": {
                "properties": {
                    "auth_token": {"type": "string"}
                }, 
                "required": ["auth_token"]
            },
            "query_assets": {
                "properties": {
                    "task": {
                        "type": "string", 
                        "description": "JENIS TUGAS. 'filter' (cari list), 'get_top_per_group' (mencari item terbanyak di setiap kategori), 'breakdown' (tabel silang), 'get_distribution_analysis' (statistik %), 'get_top_values' (ranking).",
                        "enum": ["filter", "breakdown", "get_distribution_analysis", "get_top_values", "get_top_per_group"]
                    },
                    "no_asset": {
                        "type": "string",
                        "description": "Nomor unik aset. Contoh: '100693'."
                    },
                    "serial_number": {
                        "type": "string",
                        "description": "Nomor seri perangkat (Serial Number)."
                    },
                    "nama_aset": {
                        "type": "string",
                        "description": "Nama perangkat, misal: 'SERVER', 'PRINTER', 'ROUTER'."
                    },
                    "manufaktur": {
                        "type": "string", 
                        "description": "Brand atau Merk aset. Contoh: 'DELL', 'HP', 'CISCO'."
                    },
                    "area": {
                        "type": "string",
                        "description": "Filter area. Gunakan 'COASTAL' atau 'BENGKALIS' untuk Dumai, 'DURI' untuk Duri."
                    },
                    "kode_lokasi_sap": {
                        "type": "string",
                        "description": "Kode lokasi unik dari SAP. Contoh: 'ROKFLDOFC'."
                    },
                    "kondisi": {
                        "type": "string", 
                        "description": "Kondisi fisik aset. Gunakan 'Tidak Ditemukan' untuk mencari aset yang hilang/tidak ada saat inventarisasi."
                    },
                    "kondisi_not": {
                        "type": "string",
                        "description": "Kecualikan kondisi tertentu. Contoh: 'Baik' (berarti mencari yang tidak baik)."
                    },
                    "hasil_inventory": {
                        "type": "string",
                        "description": "Status kecocokan data. WAJIB gunakan 'Match' atau 'Not Match'. JANGAN gunakan istilah lain."
                    },
                    "nilai_aset_min": {
                        "type": "integer",
                        "description": "Filter harga minimal (angka saja)."
                    },
                    "nilai_aset_max": {
                        "type": "integer",
                        "description": "Filter harga maksimal (angka saja)."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Cari aset SETELAH tanggal ini (Format: YYYY-MM-DD)."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Cari aset SEBELUM tanggal ini (Format: YYYY-MM-DD)."
                    },
                    "calculation": {
                        "type": "string",
                        "enum": ["count", "sum_value"],
                        "description": "Gunakan 'count' untuk menghitung jumlah unit, 'sum_value' untuk total nilai uang."
                    },
                    "group_by_field": {
                        "type": "string", 
                        "description": "Kolom untuk pengelompokan (AREA, KONDISI, MANUFACTURE)."
                    },
                    "count_field": {
                        "type": "string", 
                        "description": "Kolom yang dihitung jumlahnya (default: 'NO ASSET')."
                    },
                    "sort_by": {
                        "type": "string",
                        "description": "Urutkan berdasarkan kolom: 'NILAI ASET', 'TANGGAL INVENTORY', atau 'NO ASSET'."
                    },
                    "sort_direction": {
                        "type": "string",
                        "enum": ["ascending", "descending"],
                        "default": "ascending"
                    },
                    "limit": {
                        "type": "integer", 
                        "default": 10
                    }
                }
            },
            "query_resource": {
                "properties": {
                    "resource_name": {"type": "string"},
                    "area": {"type": "string"},
                    "kondisi": {"type": "string"}
                },
                "required": ["resource_name"]
            },
            "get_stats_data": {
                "properties": {
                    "timestamp": {
                        "type": "string",
                        "description": "Timestamp analisis yang ingin diambil. Gunakan 'temporary' untuk data terbaru yang belum disimpan."
                    },
                    "area": {
                        "type": "string",
                        "description": "Filter area. Contoh: 'COASTAL', 'DURI', 'MINAS', atau 'Semua Area'."
                    }
                }
            },
            "get_master_data": {
            "properties": {
                "sheet_name": {"type": "string", "default": "MasterDataAsset"}
            }
            },
            "get_all_users": {
                "properties": {}
            },
            "get_sheet_names": {"properties": {}},
            "get_history": {"properties": {}},
            "delete_history": {
                "properties": {
                    "timestamp": {"type": "string"}
                }, 
                "required": ["timestamp"]
            }
        }
    
    def _validate_tool_arguments(self, tool_name: str, arguments: dict):
            schemas = self._get_tool_schemas()
            if tool_name not in schemas: 
                raise ValueError(f"Tool '{tool_name}' unknown.")
            
            # --- PERBAIKAN: Auto-Fix untuk Task Breakdown ---
            if tool_name == "query_assets" and arguments.get("task") == "breakdown":
                if not arguments.get("group_by_field"):
                    if arguments.get("kode_lokasi_sap"):
                        arguments["group_by_field"] = "KODE LOKASI SAP"
                    elif arguments.get("area"):
                        arguments["group_by_field"] = "AREA"
                
                if not arguments.get("count_field"):
                    arguments["count_field"] = "NO ASSET"

    async def _handle_initialize(self, params: dict, db_session, websocket: WebSocket) -> dict:
        return {
            "protocolVersion": self.protocol_version, 
            "capabilities": self.capabilities, 
            "serverInfo": self.server_info
        }

    async def _handle_tools_list(self, params: dict, db_session, websocket: WebSocket) -> dict:
        tool_schemas = self._get_tool_schemas()
        descriptions = {
            "trigger_analysis": "HANYA digunakan untuk merefresh atau membuat ulang Dashboard Analisis utama secara keseluruhan. Tool ini tidak memberikan teks jawaban langsung ke chat.",
            "query_assets": "Mencari, memfilter, atau membuat breakdown statistik dari data aset utama. PENTING: Untuk area Dumai gunakan 'COASTAL', untuk kondisi rusak gunakan 'Rusak Berat, Rusak Ringan'.",
            "query_resource": "Mencari data spesifik dari hasil analisis (file JSON) yang sudah disimpan sebelumnya.",
            "save_analysis": "Menyimpan hasil analisis terbaru ke dalam database riwayat.",
            "get_dashboard_data": "Mengambil data ringkasan cepat untuk tampilan dashboard.",
            "get_sheet_names": "Mendapatkan daftar nama sheet yang tersedia di Google Sheets.",
            "get_master_data": "Mengambil seluruh data mentah dari sheet tertentu.",
            "get_all_users": "Mengambil daftar seluruh pengguna sistem (hanya untuk Admin).",
            "create_user": "Membuat akun pengguna baru di sistem dan Firebase (Hanya untuk Admin).",
            "delete_user": "Menghapus akun pengguna dari database sistem dan Firebase berdasarkan ID (Hanya untuk Admin).",
            "update_user_email": "Mengubah alamat email pengguna yang sudah ada (Hanya untuk Admin).",
            "update_user_role": "Mengubah peran/akses pengguna, misalnya dari 'user' menjadi 'admin' (Hanya untuk Admin).",
            "get_history": "Mendapatkan riwayat analisis yang pernah dilakukan.",
            "delete_history": "Menghapus riwayat analisis berdasarkan timestamp.",
            "get_stats_data": "Mengambil data statistik detail untuk halaman Statistik, dengan opsi filter area dan timestamp."
        }
        
        tools = [
            {
                "name": name, 
                "description": descriptions.get(name, ""), 
                "inputSchema": {"type": "object", **schema}
            } for name, schema in tool_schemas.items()
        ]
        return {"tools": tools}

    async def _handle_tools_call(self, params: dict, db_session, websocket: WebSocket) -> Optional[dict]:
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name: 
            raise ValueError("Tool name is required.")
        
        self._validate_tool_arguments(tool_name, arguments)
        
        # Mapping Tool Name ke Use Case Name
        tool_map = {
            "get_dashboard_data": "get_dashboard_data",
            "trigger_analysis": "trigger_analysis",
            "save_analysis": "save_latest_analysis",
            "get_history": "get_all_history",
            "delete_history": "delete_history",
            "get_sheet_names": "get_sheet_names",
            "get_master_data": "get_master_data", 
            "get_all_users": "get_all_users",   
            "create_user": "create_user",         
            "delete_user": "delete_user",         
            "update_user_email": "update_user_email", 
            "update_user_role": "update_user_role",     
            "query_assets": "query_assets",
            "query_resource": "query_resource",
            "get_stats_data": "get_stats_data",
        }
        
        use_case_name = tool_map.get(tool_name)
        if not use_case_name: 
            raise ValueError(f"No use case mapped for tool '{tool_name}'.")

        # LOGIKA KHUSUS: Trigger Analysis (Background Task dengan Progress)
        if tool_name == "trigger_analysis":
            use_case_args = {'options': AnalysisOptions(**arguments)}
            
            async def send_progress_update(progress: Dict):
                await websocket.send_json({
                    "jsonrpc": "2.0", 
                    "method": "analysis/progress", 
                    "params": progress
                })

            def run_analysis_sync():
                # Buat session baru khusus untuk thread ini
                thread_db_session = SessionLocal()
                try:
                    use_case = self.container.get_use_case("trigger_analysis", thread_db_session)
                    use_case.execute(**use_case_args, progress_callback=send_progress_update_sync)
                finally:
                    thread_db_session.close()

            loop = asyncio.get_event_loop()
            def send_progress_update_sync(progress: Dict):
                asyncio.run_coroutine_threadsafe(send_progress_update(progress), loop)

            # Jalankan di thread pool agar tidak memblokir event loop utama
            loop.run_in_executor(None, run_analysis_sync)
            return None

        # LOGIKA UMUM: Eksekusi Use Case
        use_case_args = arguments
        if tool_name == 'save_analysis':
            token = arguments.get("auth_token")
            user_repo = get_user_repository(db_session)
            current_user = get_current_user_from_token(token, user_repo)
            use_case_args = {'current_user': current_user}

        try:
            use_case = self.container.get_use_case(use_case_name, db_session)
            # Handle sync execution
            result = use_case.execute(**use_case_args)
            
            # JSON Serializer untuk tipe data kompleks
            def json_converter(o):
                if is_dataclass(o): 
                    return asdict(o)
                if isinstance(o, datetime): 
                    return o.isoformat()
                if isinstance(o, Enum): 
                    return o.value
                return str(o)

            result_str = json.dumps(result, default=json_converter)
            return {
                "content": json.loads(result_str), 
                "isError": False
            }
            
        except Exception as e:
            logging.error(f"Error executing {tool_name}: {e}")
            raise ValueError(f"Execution failed: {e}")

    async def _handle_resources_list(self, params: dict, db_session, websocket: WebSocket) -> dict:
        use_case = self.container.get_use_case("get_resources", db_session)
        resources = [
            {
                "uri": f"phr://resource/{res['name']}", 
                "name": res["name"], 
                "mimeType": "application/json"
            } for res in use_case.execute()
        ]
        return {"resources": resources}

    async def _handle_resources_read(self, params: dict, db_session, websocket: WebSocket) -> dict:
        uri = params.get("uri")
        if not uri or not uri.startswith("phr://resource/"): 
            raise ValueError("Invalid Resource URI.")
        
        filename = uri.replace("phr://resource/", "")
        file_repo = self.container.get_use_case("get_resources", db_session).file_repo
        file_entity = file_repo.find_by_filename(filename)
        
        if not file_entity or not file_entity.json_content:
            raise ValueError(f"Resource '{filename}' not found.")
            
        return {
            "contents": [{
                "uri": uri, 
                "mimeType": "application/json", 
                "text": file_entity.json_content
            }]
        }

    async def _handle_prompts_list(self, params: dict, db_session, websocket: WebSocket) -> dict:
        use_case = self.container.get_use_case("get_prompts", db_session)
        return {"prompts": use_case.execute()}

    async def _handle_prompts_get(self, params: dict, db_session, websocket: WebSocket) -> dict:
        name = params.get("name")
        arguments = params.get("arguments", {})
        use_case = self.container.get_use_case("get_prompts", db_session)
        template = use_case.get_prompt_template(name)
        
        if not template: 
            raise ValueError(f"Prompt '{name}' not found.")
        
        return {
            "messages": [{
                "role": "user", 
                "content": {
                    "type": "text", 
                    "text": template.format(**arguments)
                }
            }]
        }