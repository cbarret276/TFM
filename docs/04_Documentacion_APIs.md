# 04 - Documentación de APIs

### APIs integradas

- **Hatching Triage**
  - Endpoint: `/search/submissions`
  - Autenticación: Token en cabecera
  - Atributos usados: family, score, ttp, tags

- **Malware Bazaar**
  - Endpoint: `/query/get_recent`
  - Autenticación: pública
  - Atributos: sha256, delivery_method, origin_country

- **ThreatFox**
  - Endpoint: `/api/v1/`
  - Autenticación: API key
  - Atributos: threat_type, confidence_level, first_seen, malware

### Herramienta de prueba

Durante el desarrollo se utilizó [Hoppscotch.io](https://hoppscotch.io) para probar endpoints y validar autenticación y respuestas JSON.
