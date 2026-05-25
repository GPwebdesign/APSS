# APSS — Script Documentazione Tecnica

## gen_doc_apss.mjs

Script Node.js per generare `APSS_Documentazione_Tecnica_vX_Y.docx`.

### Setup (una volta sola)
```bash
cd D:\_claudecodeproject\APSS\docs\scripts
npm install docx
```

### Uso per aggiornare la documentazione
```bash
# 1. Modifica gen_doc_apss.mjs — aggiorna solo le sezioni cambiate
# 2. Esegui
node gen_doc_apss.mjs
# 3. Copia l'output in docs/
copy APSS_Documentazione_Tecnica_v2_5.docx ..\
```

### Delegare a Claude Code (zero token in chat)
Prompt da usare:
```
Sei in D:\_claudecodeproject\APSS\docs\scripts\
Modifica gen_doc_apss.mjs aggiornando [sezione X] con [nuovo contenuto].
Aggiorna il numero versione nella copertina (vX.Y) e nel registro revisioni.
Poi esegui: node gen_doc_apss.mjs
L'output va salvato in D:\_claudecodeproject\APSS\docs\ come APSS_Documentazione_Tecnica_vX_Y.docx
```

### Note tecniche
- Formato A4 portrait, font Calibri, tema colori APSS (blu 2E75B6)
- Tabelle con header blu, righe alternate, note box azzurre/verdi
- NON usare PageNumber di docx-js — non supportato in questa versione
- Colori hex SEMPRE 6 caratteri (es. '595959' non '5959')
- Testato con docx npm package (qualsiasi versione recente)

### Versioni prodotte
| File | Versione | Data |
|---|---|---|
| APSS_Documentazione_Tecnica_v2_4.docx | v2.4 | Maggio 2026 |
