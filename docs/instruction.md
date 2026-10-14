# Ingesting data

- Download the dataset from the URL in `data/source/data.txt` and save it as
  `data/raw/dynamic_supply_chain_logistics_dataset.csv`. The ingestion script
  also accepts the existing `data/row` directory for compatibility.
- create and  EC2 Instance > docker container > mcr.microsoft.com/mssql/server:2022-latest
- Spin up the Legacy MSSQL Server

Install Microsoft ODBC Driver 18 for SQL Server on Windows before running the
ingestion script. The script can also use the legacy `SQL Server` driver when
Driver 17 or 18 is not installed.
```
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=FdeEnterprisePass123!" -p 1433:1433 --name legacy-mssql -d mcr.microsoft.com/mssql/server:2022-latest

# or multi-line in windows 
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=FdeEnterprisePass123!" ^
   -p 1433:1433 --name legacy-mssql ^
   -d mcr.microsoft.com/mssql/server:2022-latest

# or multi-line unix
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=FdeEnterprisePass123!" \
   -p 1433:1433 --name legacy-mssql \
   -d mcr.microsoft.com/mssql/server:2022-latest

# or multi-line with volume inside EC2
docker run -v mssql_data:/var/opt/mssql \
  -e "ACCEPT_EULA=Y" \
  -e "MSSQL_SA_PASSWORD=FdeEnterprisePass123!" \
  -p 1433:1433 \
  --name legacy-mssql \
  -d mcr.microsoft.com/mssql/server:2022-latest

```

# Phase 1

## SOP Ingestion

- https://app.pinecone.io/ > Get api key
