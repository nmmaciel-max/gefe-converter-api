import os
import shutil
import subprocess
import tempfile
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI(title="GEFE 2.0 Migration Engine")

# Credenciais padrão GEFE 1.0
ACCESS_USER = "PG5MasterDBA"
ACCESS_PASS = "K9YPG5-XPB"


@app.get("/")
def health_check():
    return {"status": "ok", "service": "GEFE 2.0 Migration API"}


@app.post("/convert")
async def convert_mdb(
    mdb_file: UploadFile = File(...), mdw_file: UploadFile = File(...)
):
    with tempfile.TemporaryDirectory() as tmp_dir:

#ATENÇÃO na linha abaixo substitua o database.mdb pelo nome do banco do cliente exemplo TecEng.mdb
        mdb_path = os.path.join(tmp_dir, "database.mdb")
        mdw_path = os.path.join(tmp_dir, "system.mdw")

        # Salva os arquivos recebidos do cliente
        with open(mdb_path, "wb") as buffer:
            shutil.copyfileobj(mdb_file.file, buffer)
        with open(mdw_path, "wb") as buffer:
            shutil.copyfileobj(mdw_file.file, buffer)

        # Extração das tabelas via mdbtools (Linux/Containers)
        try:
            # Lista tabelas do banco
            cmd_tables = f"mdb-tables -1 '{mdb_path}'"
            tables_output = subprocess.check_output(
                cmd_tables, shell=True, text=True
            )
            tables = [
                t.strip()
                for t in tables_output.split("\n")
                if t.strip() and not t.startswith("MSys")
            ]

            extracted_data = {}

            # Exporta esquema e dados em formato estruturado
            for table in tables:
                cmd_dump = f"mdb-json '{mdb_path}' '{table}'"
                try:
                    json_data = subprocess.check_output(
                        cmd_dump, shell=True, text=True
                    )
                    extracted_data[table] = json_data
                except Exception as e:
                    print(f"Aviso na tabela {table}: {e}")

            return JSONResponse(
                content={
                    "status": "success",
                    "total_tables": len(tables),
                    "data": extracted_data,
                }
            )

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Erro na conversão: {str(e)}"
            )