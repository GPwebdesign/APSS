import {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  VerticalAlign, PageBreak, Header, Footer, LevelFormat
} from 'docx';
import fs from 'fs';

// ─── COLORS ───────────────────────────────────────────────────────────────────
const C = {
  BLUE:     '1F4E79',
  LBLUE:    '2E75B6',
  LLBLUE:   'D5E8F0',
  HEADER:   '1F4E79',
  ROW_ALT:  'EBF3FB',
  WHITE:    'FFFFFF',
  GRAY:     'F2F2F2',
  DGRAY:    '595959',
  BLACK:    '000000',
  GREEN:    '375623',
  LGREEN:   'E2EFDA',
  ORANGE:   'C55A11',
  LORANGE:  'FCE4D6',
};

const FONT = 'Calibri';
const PAGE_W = 11906; // A4
const MARGINS = { top: 1134, right: 1134, bottom: 1134, left: 1134 }; // ~2cm
const CONTENT_W = PAGE_W - MARGINS.left - MARGINS.right; // 9638

// ─── HELPERS ──────────────────────────────────────────────────────────────────
const border1 = (color = 'CCCCCC') => ({ style: BorderStyle.SINGLE, size: 1, color });
const allBorders = (color = 'CCCCCC') => ({ top: border1(color), bottom: border1(color), left: border1(color), right: border1(color) });
const noBorder = () => ({ style: BorderStyle.NONE, size: 0, color: 'FFFFFF' });
const noAllBorders = () => ({ top: noBorder(), bottom: noBorder(), left: noBorder(), right: noBorder() });

const txt = (text, opts = {}) => new TextRun({ text, font: FONT, size: opts.size ?? 20, bold: opts.bold ?? false, color: opts.color ?? C.BLACK, italics: opts.italics ?? false });
const para = (children, opts = {}) => new Paragraph({
  children: Array.isArray(children) ? children : [children],
  alignment: opts.align ?? AlignmentType.LEFT,
  spacing: { before: opts.before ?? 80, after: opts.after ?? 80 },
  heading: opts.heading,
  indent: opts.indent,
});

const h1 = (text) => new Paragraph({
  children: [new TextRun({ text, font: FONT, size: 28, bold: true, color: C.LBLUE })],
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 240, after: 120 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C.LBLUE, space: 1 } },
});

const h2 = (text) => new Paragraph({
  children: [new TextRun({ text, font: FONT, size: 22, bold: true, color: C.HEADER })],
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 180, after: 80 },
});

const h3 = (text) => new Paragraph({
  children: [new TextRun({ text, font: FONT, size: 20, bold: true, color: C.DGRAY })],
  heading: HeadingLevel.HEADING_3,
  spacing: { before: 120, after: 60 },
});

const bullet = (text, level = 0) => new Paragraph({
  children: [txt(text)],
  numbering: { reference: 'bullets', level },
  spacing: { before: 40, after: 40 },
});

const code = (text) => new Paragraph({
  children: [new TextRun({ text, font: 'Courier New', size: 18, color: C.DGRAY })],
  spacing: { before: 40, after: 40 },
  indent: { left: 720 },
  shading: { fill: C.GRAY, type: ShadingType.CLEAR },
});

const emptyPara = () => para(txt(''), { before: 40, after: 40 });

// ─── TABLE HELPERS ────────────────────────────────────────────────────────────
const cell = (children, opts = {}) => new TableCell({
  children: Array.isArray(children) ? children : [para(children)],
  borders: opts.borders ?? allBorders(),
  shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR } : undefined,
  width: opts.width ? { size: opts.width, type: WidthType.DXA } : undefined,
  margins: { top: 80, bottom: 80, left: 120, right: 120 },
  verticalAlign: opts.va ?? VerticalAlign.CENTER,
  columnSpan: opts.span,
});

const hdrCell = (text, width, color = C.HEADER) => cell(
  [para([txt(text, { bold: true, color: C.WHITE, size: 18 })], { before: 60, after: 60 })],
  { fill: color, width, borders: allBorders(color) }
);

const dataCell = (text, width, fill, bold = false, color = C.BLACK) => cell(
  [para([txt(text, { size: 18, bold, color })], { before: 60, after: 60 })],
  { fill: fill ?? C.WHITE, width, borders: allBorders('CCCCCC') }
);

const twoColTable = (rows, w1, w2, headerFill = C.HEADER) => {
  const tableRows = rows.map((r, i) => new TableRow({
    children: [
      dataCell(r[0], w1, i === 0 ? headerFill : (i % 2 === 0 ? C.ROW_ALT : C.WHITE), i === 0, i === 0 ? C.WHITE : C.BLACK),
      dataCell(r[1], w2, i === 0 ? C.LLBLUE : (i % 2 === 0 ? C.ROW_ALT : C.WHITE), false),
    ]
  }));
  return new Table({ width: { size: w1 + w2, type: WidthType.DXA }, columnWidths: [w1, w2], rows: tableRows });
};

const threeColTable = (headers, rows) => {
  const w = [3000, 3500, 3138];
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: w,
    rows: [
      new TableRow({ children: headers.map((h, i) => hdrCell(h, w[i])) }),
      ...rows.map((r, ri) => new TableRow({
        children: r.map((c, i) => dataCell(c, w[i], ri % 2 === 0 ? C.ROW_ALT : C.WHITE))
      }))
    ]
  });
};

const genericTable = (headers, rows, widths) => {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ children: headers.map((h, i) => hdrCell(h, widths[i])) }),
      ...rows.map((r, ri) => new TableRow({
        children: r.map((c, ci) => dataCell(c, widths[ci], ri % 2 === 0 ? C.ROW_ALT : C.WHITE))
      }))
    ]
  });
};

// ─── NOTE BOX ─────────────────────────────────────────────────────────────────
const noteBox = (text, fill = C.LLBLUE, borderColor = C.LBLUE) => new Table({
  width: { size: CONTENT_W, type: WidthType.DXA },
  columnWidths: [CONTENT_W],
  rows: [new TableRow({ children: [cell(
    [para([txt('⚠️  ' + text, { size: 18, italics: true, color: C.LBLUE })], { before: 80, after: 80 })],
    { fill, borders: allBorders(borderColor), width: CONTENT_W }
  )] })]
});

// ─── PAGE BREAK ───────────────────────────────────────────────────────────────
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

// ══════════════════════════════════════════════════════════════════════════════
// DOCUMENT CONTENT
// ══════════════════════════════════════════════════════════════════════════════

const children = [];

// ─── COVER ────────────────────────────────────────────────────────────────────
children.push(
  para([txt('APSS — Autonomous Patrol and Surveillance System', { bold: true, size: 36, color: C.LBLUE })], { align: AlignmentType.CENTER, before: 400, after: 120 }),
  para([txt('DOCUMENTAZIONE TECNICA', { bold: true, size: 28, color: C.HEADER })], { align: AlignmentType.CENTER, before: 0, after: 80 }),
  para([txt('Piattaforma Hardware: Yahboom Rosmaster R2 — ROS2 Humble — Docking Station con Ricarica Autonoma', { size: 20, color: C.DGRAY, italics: true })], { align: AlignmentType.CENTER, before: 0, after: 400 }),
);

// Copertina tabella dati
children.push(
  new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [3000, 6638],
    rows: [
      ['Revisione', 'v2.5'],
      ['Data', 'Maggio 2026'],
      ['Concept & System Designer', 'GPwebdesign — Gennaro Puzio'],
      ['AI Assistant', 'Anthropic Claude'],
      ['Stato', 'In sviluppo attivo'],
      ['Repository ROS2', 'github.com/GPwebdesign/ros2_py_ws (privato)'],
      ['Repository Rosmaster', 'github.com/GPwebdesign/rosmaster_project (privato)'],
      ['Repository APSS', 'github.com/GPwebdesign/APSS (privato)'],
    ].map((r, i) => new TableRow({ children: [
      dataCell(r[0], 3000, C.LLBLUE, true),
      dataCell(r[1], 6638, i % 2 === 0 ? C.WHITE : C.GRAY),
    ]}))
  }),
  emptyPara(),
);

// Registro revisioni
children.push(h2('Registro delle Revisioni'));
children.push(genericTable(
  ['Versione', 'Data', 'Descrizione modifiche'],
  [
    ['v1.0', 'Marzo 2026', 'Prima emissione — documentazione tecnica software e ROS2'],
    ['v1.5', 'Aprile 2026', 'Aggiunta sezione circuito di ricarica XL4016 CC/CV, XHM603 v1.0'],
    ['v1.6', 'Aprile 2026', 'App Kivy/KivyMD completa: controllo robot, stream video 31 FPS, pan/tilt'],
    ['v1.7', 'Aprile 2026', 'Rinominato progetto in APSS — Autonomous Patrol and Surveillance System'],
    ['v1.9', 'Aprile 2026', 'Piattaforma mobile proprietaria. RPLIDAR A1M8. Architettura hardware indipendente futura'],
    ['v2.1', 'Maggio 2026', 'Pipeline colore camera RGB nativo (picamera2). Endpoint /capture_still. Rimozione OpenCV obstacle avoidance'],
    ['v2.2', 'Maggio 2026', 'Batteria LiFePO4 ECO-WORTHY 8Ah. XL4016 ricalibrato. INA219 robot + battery_node. TOF400C tutti verificati OK'],
    ['v2.3', 'Maggio 2026', 'Riformattazione documento. Stack ROS2, nodi batteria, TOF, oled. Sviluppo futuro ripristinato'],
    ['v2.4', 'Maggio 2026', 'Circuito ricarica definitivo LiFePO4 (XL4016 1.5A, T3.15A, XHM603 soglie confermate). Firmware ESP32 v2.1. battery_node v2.0 coulomb counting. Dati ciclo ricarica verificati. USB device naming udev'],
    ['v2.5', 'Maggio 2026', 'Correzione INA219 robot: distinzione PSU esterna vs batteria reale. Aggiornamento roadmap firmware v2.2 microswitch.'],
  ],
  [1200, 1600, 6838]
));

children.push(pageBreak());

// ─── SEZ 1 — SOMMARIO ─────────────────────────────────────────────────────────
children.push(h1('1. Sommario Esecutivo'));
children.push(para([txt('APSS (Autonomous Patrol and Surveillance System) è un sistema autonomo di pattugliamento e sorveglianza per ambienti interni (appartamento). La piattaforma mobile è una struttura proprietaria progettata e realizzata dal system designer, che integra componenti Yahboom Rosmaster R2 (scheda espansione STM32, motori DC encoder Mecanum) con Raspberry Pi 4 come elaboratore principale.')]));
children.push(emptyPara());
children.push(para([txt('Il sistema è equipaggiato con camera CSI Arducam OV5647 con IR-cut motorizzato automatico, servo pan/tilt, RPLIDAR A1M8 Slamtec, 3 sensori TOF400C VL53L1X, display OLED SSD1306, sensori ambientali e batteria ECO-WORTHY LiFePO4 12.8V 8Ah come unica fonte di energia.')]));
children.push(emptyPara());
children.push(para([txt('Il sistema è controllabile da remoto tramite l\'app Kivy/KivyMD sviluppata per Linux/Windows/Android, che fornisce stream video in tempo reale a 31 FPS, controllo motori Mecanum, controllo pan/tilt, acquisizione foto still ad alta qualità e registrazione video.')]));
children.push(emptyPara());
children.push(para([txt('Nota architetturale: in uno sviluppo futuro i componenti Yahboom Rosmaster R2 potranno essere sostituiti da una architettura open hardware completamente personalizzabile. Vedere Sezione 11.1.', { italics: true, color: C.DGRAY })]));

children.push(h2('1.1 Obiettivi del Progetto'));
[
  'Navigazione autonoma con obstacle avoidance basato su RPLIDAR A1M8 e sensori TOF400C VL53L1X',
  'Sistema di pattugliamento con rilevamento movimento e streaming video remoto',
  'Sistema di sorveglianza autonomo con sensori ambientali (DHT-11, microfono, gas) — architettura scalabile via MQTT',
  'Docking autonomo con ricarica automatica tramite pogo pin e marker ArUco',
  'Monitoraggio continuo stato batteria e gestione autonoma cicli ricarica',
  'Interfaccia app Kivy multipiattaforma (Linux/Windows/Android) per controllo remoto e monitoraggio',
].forEach(b => children.push(bullet(b)));

// ─── SEZ 2 — ARCHITETTURA ─────────────────────────────────────────────────────
children.push(h1('2. Architettura di Sistema'));
children.push(genericTable(
  ['Sottosistema', 'Componenti principali'],
  [
    ['Robot mobile', 'Struttura proprietaria GPwebdesign + Raspberry Pi 4 + Camera OV5647 IR-cut + Pan/Tilt servo + RPLIDAR A1M8 + 3x TOF400C VL53L1X + OLED SSD1306 + Batteria ECO-WORTHY LiFePO4 12.8V 8Ah + 4 motori DC Mecanum + INA219 monitor alimentazione + DD32AJ4B convertitore multi-uscita'],
    ['Docking station', 'Alimentatore 230V/20V + Relay ESP32 GPIO5 + XL4016 CC/CV (14.40V/1.5A) + Fusibile T3.15A slow-blow + XHM603 v1.0 + INA219 HW-831B + Pogo pin + Microswitch NC + ESP32 MicroPython firmware v2.1'],
    ['App controllo', 'Kivy 2.3.1 + KivyMD 1.2.0 — Linux/Windows/Android — stream video 31 FPS + /capture_still + APK Android debug 2.1 (testato Samsung S23 Ultra)'],
    ['Comunicazione', 'TCP socket porta 6000 (controllo) + HTTP porta 6500 (stream MJPEG + /capture_still)'],
    ['Software robot', 'ROS2 Humble — Ubuntu 22.04 — Python 3.10 — rosmaster_main.py V2.3.3'],
    ['Software stazione', 'MicroPython su ESP32 — firmware v2.1 — dashboard http://192.168.1.193'],
  ],
  [3000, 6638]
));

// ─── SEZ 3 — CIRCUITO RICARICA ────────────────────────────────────────────────
children.push(pageBreak());
children.push(h1('3. Hardware — Circuito di Ricarica'));
children.push(para([txt('Il circuito di ricarica è stato progettato, assemblato, testato e calibrato. Tutti i parametri riportati in questa sezione sono stati verificati con strumentazione di misura reale. Il circuito è operativo e autonomo: la ricarica avviene automaticamente senza intervento manuale.')]));

children.push(h2('3.1 Architettura del Circuito (v2.4 — definitiva)'));
children.push(code('220VAC → [Alimentatore 20V/3.25A] → [Relay CH1 ESP32 GPIO5]'));
children.push(code('       → [XL4016 CC/CV 14.40V/1.5A] → [Fusibile T3.15A slow-blow]'));
children.push(code('       → [XHM603 v1.0] → [INA219 HW-831B] → [Pogo pin]'));
children.push(code('       → [Pad rame robot] → [ECO-WORTHY LiFePO4 12.8V 8Ah]'));
children.push(emptyPara());

children.push(genericTable(
  ['Componente', 'Dettaglio', 'Stato'],
  [
    ['Alimentatore', '220VAC → 20VDC 3.25A — switching', '✅ Operativo'],
    ['Relay ricarica', 'ESP32 GPIO5 — LOW=chiuso (ricarica abilitata), HIGH=aperto (bloccata)', '✅ Operativo'],
    ['Step-down XL4016', 'CC/CV — CV=14.40V, CC=1.5A — calibrati Maggio 2026', '✅ Calibrato'],
    ['Fusibile', 'T3.15A 250V slow-blow — in serie sul positivo', '✅ Installato'],
    ['Controller ricarica', 'XHM603 v1.0 — START 13.1V / STOP 14.4V display — LiFePO4', '✅ Calibrato'],
    ['Batteria', 'ECO-WORTHY LiFePO4 12.8V 8Ah (ECO-LFPYZ1208) — sostituisce Yuasa YTZ10S AGM', '✅ Installata'],
    ['Monitor ricarica', 'INA219 HW-831B — I2C 0x40 su ESP32 — VIN+ ← XHM603, VIN- → pogo pin', '✅ Operativo'],
    ['Connettore ricarica', 'Pogo pin a molla orizzontali → pad rame robot 152x65x96mm', '✅ Operativo'],
    ['Rilevamento docking', 'Microswitch meccanico NC GPIO18 — sostituisce reed switch (comportamento erratico)', '⚠️ Fissato aperto'],
  ],
  [2800, 4900, 1938]
));

children.push(emptyPara());
children.push(noteBox('Nota tecnica — corrente CC 1.5A: corrente di 2A genera spike alla chiusura del relay che fa scattare erroneamente XHM603. 1.5A è il valore di compromesso ottimale verificato sperimentalmente. Il tasso di carica risultante è 0.19C su batteria da 8Ah — conservativo e benefico per la longevità delle celle.'));

children.push(h2('3.2 Parametri XHM603 v1.0 — Soglie Definitive LiFePO4'));
children.push(para([txt('Le soglie riportate di seguito sono state determinate empiricamente attraverso cicli di ricarica completi con strumentazione di misura in linea (tester + INA219). I valori sono definitivi e non richiedono ulteriore calibrazione.')]));
children.push(emptyPara());

children.push(genericTable(
  ['Parametro', 'Valore display', 'Tensione reale stimata', 'Note'],
  [
    ['Soglia STOP (fine carica)', '14.4V display', '~13.70–13.80V ai terminali', 'Scatta al SUPERAMENTO → effettivo a 14.5V display'],
    ['Soglia START (avvia ricarica)', '13.1V display', '~12.40V ai terminali', 'Avvia ricarica a ~20% SoC LiFePO4'],
  ],
  [2500, 2000, 2500, 2638]
));

children.push(emptyPara());
children.push(noteBox('Comportamento XHM603: la soglia scatta al SUPERAMENTO del valore impostato — impostato 14.4V → scatta a 14.5V display. Misurare tensione con tester sui terminali batteria DURANTE la ricarica può far scattare il relay per perturbazione del circuito — riarmare manualmente da webapp ESP32 http://192.168.1.193.'));

children.push(h2('3.3 Offset Catena di Potenza Docking'));
children.push(para([txt('Offsets misurati fisicamente con tester e INA219 durante sessioni di ricarica reali (Maggio 2026):')]));
children.push(emptyPara());

children.push(genericTable(
  ['Coppia', 'Offset misurato', 'Condizione di misura'],
  [
    ['Display XHM603 vs terminali batteria', '+0.70V', 'Relay aperto (circuito a vuoto)'],
    ['INA219 docking vs terminali batteria', '+0.34V', 'In ricarica attiva (~1.35A)'],
    ['Display XHM603 vs INA219 docking', '+0.40V', 'In ricarica attiva'],
  ],
  [3500, 2500, 3638]
));

children.push(h2('3.4 Dati Ciclo di Ricarica Completo — Verificati Maggio 2026'));
children.push(para([txt('Dati rilevati durante il primo ciclo di ricarica completo con batteria ECO-WORTHY LiFePO4 e circuito definitivo calibrato:')]));
children.push(emptyPara());

children.push(genericTable(
  ['Parametro', 'Valore misurato', 'Note'],
  [
    ['OCV inizio ciclo', '13.23V', '~60-70% SoC — batteria parzialmente scarica'],
    ['Durata ricarica completa', '~3 ore', 'Da ~60% a ~95% SoC a 1.5A'],
    ['Corrente fase CC (constant current)', '~1.35A media', 'XL4016 in modalità CC'],
    ['Corrente fine carica (fase CV)', '~0.99A al momento scatto', 'XL4016 passa in modalità CV — corrente in discesa'],
    ['Display XHM603 al momento scatto', '14.5V', 'Soglia 14.4V + superamento confermato'],
    ['OCV post-scatto immediato', '13.60V', 'Tensione rimbalza dopo interruzione corrente'],
    ['OCV stabile (30 min post-carica)', '13.40V', '~95% SoC — soglia STOP corretta, non modificare'],
  ],
  [3500, 2500, 3638]
));

children.push(emptyPara());
children.push(noteBox('Valutazione soglia STOP: con OCV stabile a 13.40V (30 min post-carica) corrispondente a ~95% SoC, la soglia STOP a 14.4V display è corretta. Non è necessario alzarla ulteriormente.', C.LGREEN, C.GREEN));

// ─── SEZ 4 — HARDWARE ROBOT ───────────────────────────────────────────────────
children.push(pageBreak());
children.push(h1('4. Hardware — Robot Mobile'));

children.push(h2('4.1 Piattaforma e Componenti Principali'));
children.push(para([txt('La piattaforma mobile è una struttura proprietaria progettata e realizzata dal system designer. Integra componenti Yahboom Rosmaster R2 (scheda espansione, motori) con hardware aggiuntivo selezionato per le specifiche esigenze del progetto APSS.')]));
children.push(emptyPara());

children.push(genericTable(
  ['Componente', 'Modello / Tipo', 'Note'],
  [
    ['Piattaforma mobile', 'Struttura proprietaria GPwebdesign', 'Telaio custom — ruote Mecanum configurazione X'],
    ['Elaboratore principale', 'Raspberry Pi 4', 'Ubuntu 22.04.5 LTS aarch64 — hostname: hawk — IP: 192.168.1.158'],
    ['Scheda espansione', 'Yahboom Rosmaster Expansion Board V3.0', 'STM32F103RCT6 — IMU MPU9250'],
    ['Convertitore alimentazione', 'DD32AJ4B multi-output', 'Setpoint 12.16V a vuoto — alimenta scheda Yahboom + RPi. INA219 robot posizionato a valle'],
    ['Motori ruote', '4x motori DC encoder Yahboom', 'M1=ant.sx, M2=ant.dx, M3=post.sx, M4=post.dx — ENCODER_CPR=822'],
    ['Camera', 'Arducam OV5647 CSI IR-cut (B07X1VGQSL)', 'IR-cut automatico via LDR — fuoco fisso 0-1.5m — 31 FPS 640x480'],
    ['Pan/Tilt', '2x servo PWM', 'S1=Tilt, S2=Pan (swap fisico) — home: pan=100°, tilt=85°'],
    ['LiDAR', 'Slamtec RPLIDAR A1M8', '360° — range 0.15-12m — /dev/rplidar (symlink udev) — offset fisico 90°'],
    ['Sensori TOF', '3x TOF400C VL53L1X', 'Frontale 0° (CH2) + sx 30° (CH3) + dx 30° (CH4) — tutti verificati OK (0x29)'],
    ['Multiplexer I2C', 'TCA9548A — indirizzo 0x70', 'Gestisce 3x TOF400C su CH2/CH3/CH4'],
    ['Monitor alimentazione', 'INA219 — indirizzo 0x40', 'In serie al positivo — shunt R100 — posizionato DOPO DD32AJ4B. Con batteria LiFePO4 reale segue la tensione reale (<12.0V anche a batteria carica)'],
    ['Display OLED', 'SSD1306 128x64 I2C — 0x3C', 'IP, tensione, corrente, potenza — oled_node.py'],
    ['Batteria di bordo', 'ECO-WORTHY LiFePO4 12.8V 8Ah (ECO-LFPYZ1208)', '152x65x96mm — terminali F2 — 1.05kg — sostituisce Yuasa YTZ10S AGM 8.6Ah'],
  ],
  [2800, 3000, 3838]
));

children.push(emptyPara());
children.push(noteBox('Nota architetturale INA219 robot: L\'INA219 è posizionato dopo il convertitore DD32AJ4B. Con alimentazione da PSU esterna (20V) al posto della batteria, misura la tensione regolata dal DD32AJ4B (~12.10V stabili). Con batteria LiFePO4 reale collegata, l\'INA219 legge stabilmente sotto 12.0V anche a batteria carica e SEGUE la tensione reale della batteria. BatteryState.voltage è quindi un segnale utile per soglie e ancoraggio SoC. Il battery_node.py usa coulomb counting come metodo primario di stima SoC.'));

children.push(h2('4.2 Mappatura Motori Mecanum — Verificata Fisicamente'));
children.push(genericTable(
  ['Porta scheda', 'Posizione fisica', 'Note polarità'],
  [
    ['M1', 'Anteriore sinistro', 'Polarità fisica invertita (fili M+/M- scambiati sul connettore)'],
    ['M2', 'Anteriore destro', 'Polarità normale'],
    ['M3', 'Posteriore sinistro', 'Polarità normale'],
    ['M4', 'Posteriore destro', 'Polarità fisica invertita (fili M+/M- scambiati sul connettore)'],
  ],
  [2000, 3000, 4638]
));
children.push(emptyPara());
children.push(para([txt('M1 e M4 richiedono polarità invertita perché il firmware STM32 usa una cinematica interna incompatibile con il cablaggio fisico del robot. Soluzione: inversione fisica dei fili M+/M- sul connettore + fattore di calibrazione m1=0.60 in motor_calibration.json.')]));

children.push(h2('4.3 Cinematica Mecanum — Implementazione Custom'));
children.push(para([txt('La funzione set_car_motion() della libreria Rosmaster non produce i movimenti corretti con il cablaggio fisico del robot. È stata implementata una cinematica custom che usa direttamente set_motor() via cmd TCP 0x1A.')]));
children.push(emptyPara());

children.push(genericTable(
  ['Variabile', 'Formula', 'Nota'],
  [
    ['M1 (ant. sinistro) — fattore 0.60', 'vx - vy + vz', 'Polarità invertita fisicamente'],
    ['M2 (ant. destro)', 'vx + vy - vz', 'Polarità normale'],
    ['M3 (post. sinistro)', 'vx + vy + vz', 'Polarità normale'],
    ['M4 (post. destro)', 'vx - vy - vz', 'Polarità invertita fisicamente'],
  ],
  [3000, 2500, 4138]
));
children.push(emptyPara());
children.push(para([txt('vx = avanti/indietro (+avanti), vy = laterale (+destra), vz = rotazione (+orario). Speed base=55. Formula verificata fisicamente. Strafe laterale puro non ottenibile — sostituito con rotazioni strette.')]));

children.push(h2('4.4 Monitor Alimentazione — INA219 Robot'));
children.push(genericTable(
  ['Parametro', 'Valore'],
  [
    ['Indirizzo I2C', '0x40'],
    ['Shunt', 'R100 (0.1Ω)'],
    ['Libreria', 'adafruit-circuitpython-ina219'],
    ['Posizione nella catena', 'Dopo DD32AJ4B — con PSU esterna misura ~12.10V stabili; con batteria LiFePO4 reale segue la tensione reale (<12.0V anche a batteria carica). BatteryState.voltage utile per soglie e ancoraggio SoC'],
    ['Convenzione corrente', 'Positiva = DISCHARGING (robot assorbe), Negativa = CHARGING (docking)'],
    ['Potenza', 'Calcolata come V × I (registro power non calibrato)'],
    ['Assorbimento idle misurato', '~0.45–0.60 A / ~5.5–7.7 W (a seconda dei carichi attivi)'],
    ['Picco in movimento (campionato a 0.5Hz)', '~2.14 A / ~25.7 W — picchi reali stimati 3-4A sub-secondo'],
  ],
  [4000, 5638]
));

// ─── SEZ 5 — HARDWARE DOCKING ─────────────────────────────────────────────────
children.push(pageBreak());
children.push(h1('5. Hardware — Docking Station'));
children.push(genericTable(
  ['Componente', 'Funzione'],
  [
    ['Alimentatore switching 220VAC → 20VDC 3.25A', 'Alimentazione primaria circuito di ricarica'],
    ['Relay CH1 ESP32 GPIO5', 'Abilita/disabilita il flusso di corrente verso XL4016. LOW=chiuso=ricarica. Si chiude automaticamente al boot se rete presente (firmware v2.1)'],
    ['Step-down XL4016 CC/CV', 'Regolazione 14.40V / 1.5A per ricarica LiFePO4 — calibrato Maggio 2026'],
    ['Fusibile T3.15A 250V slow-blow', 'Protezione linea — sostituisce T1.5A precedente'],
    ['Controller ricarica XHM603 v1.0', 'Gestione automatica ciclo carica START/STOP — soglie 13.1V / 14.4V display — scatta al superamento'],
    ['Microcontrollore ESP32 WROOM-32D', 'Monitoraggio, controllo relay automatico, dashboard web v2.1 — http://192.168.1.193'],
    ['Sensore V/I INA219 HW-831B I2C 0x40', 'Lettura tensione, corrente, potenza catena di ricarica. VIN+ ← XHM603, VIN- → pogo pin'],
    ['Connettore ricarica pogo pin 2-pin 5A', 'Trasferimento energia alla batteria LiFePO4 del robot'],
    ['Microswitch meccanico NC GPIO18', 'Rilevamento docking fisico — sostituisce reed switch (comportamento erratico). Attualmente fissato in posizione aperta in attesa di montaggio definitivo sul paraurti robot'],
    ['Partitore tensione GPIO34', 'R1=47kΩ + R2=10kΩ — rileva blackout rete 230V. V_misura=3.51V con rete presente'],
    ['Marker ArUco', 'Guida visiva per docking autonomo preciso (Fase 7 — pianificato)'],
  ],
  [3500, 6138]
));

// ─── SEZ 6 — APP KIVY ─────────────────────────────────────────────────────────
children.push(h1('6. App Kivy — Controllo Remoto'));
children.push(para([txt('L\'app di controllo è sviluppata con Kivy 2.3.1 e KivyMD 1.2.0. Gira su Linux, Windows e Android. Implementa stream video MJPEG in tempo reale, controllo motori Mecanum, pan/tilt camera, acquisizione foto still e registrazione video.')]));

children.push(h2('6.1 Stack Tecnologico'));
children.push(genericTable(
  ['Componente', 'Versione / Dettaglio'],
  [
    ['Framework UI', 'Kivy 2.3.1 + KivyMD 1.2.0 — titolo: Autonomous Patrol and Surveillance System'],
    ['Tema', 'Dark theme — portrait — toolbar: APSSystem'],
    ['Comunicazione robot', 'TCP socket porta 6000 — protocollo Yahboom ASCII hex'],
    ['Stream video', 'HTTP MJPEG porta 6500 — /video_feed — 31 FPS 640x480 — colori RGB corretti'],
    ['Still photo', 'HTTP GET porta 6500 — /capture_still — JPEG qualità 95'],
    ['Controllo motori', 'Cmd TCP 0x1A custom — cinematica Mecanum Python — speed base=55'],
    ['Controllo servo', 'Cmd TCP 0x11 — S1=Tilt, S2=Pan'],
    ['APK Android', 'apssystem-2.1-arm64-v8a_armeabi-v7a-debug.apk — Buildozer 1.5.0 — API 34 — testato Samsung S23 Ultra'],
    ['Salvataggio media Android', '/sdcard/DCIM/APSSystem/ — popup conferma — notifica MediaStore'],
  ],
  [3000, 6638]
));

children.push(h2('6.2 Schermate'));
children.push(genericTable(
  ['Schermata', 'Funzione', 'Stato'],
  [
    ['MainScreen', 'Stream video + pad controllo motori 3x3', 'Operativa'],
    ['CameraScreen', 'Stream video + controllo pan/tilt camera + still photo', 'Operativa'],
    ['SettingsScreen', 'Configurazione IP robot e porte TCP/stream', 'Operativa'],
    ['PatrolScreen', 'Gestione pattugliamento autonomo e waypoint', 'Placeholder — Fase 5'],
    ['AlertScreen', 'Log alert intrusione e clip video', 'Placeholder — Fase 6'],
    ['StatusScreen', 'Stato sistema, batteria, sensori', 'Placeholder — Fase 7'],
  ],
  [2500, 4500, 2638]
));

children.push(h2('6.3 Protocollo TCP — Comandi Implementati'));
children.push(genericTable(
  ['Comando', 'Formato', 'Funzione'],
  [
    ['Inizializzazione', '$020f040116#', 'Imposta car_type=2, g_mode=Standard — obbligatorio dopo connessione'],
    ['Movimento motori (0x1A)', '$02 1A 0C [m1][m2][m3][m4] 00 [cs]#', 'set_motor diretto con cinematica Mecanum custom'],
    ['Servo PWM (0x11)', '$02 11 06 [id][angle][cs]#', 'Controllo servo pan/tilt — id: 1=Tilt, 2=Pan'],
    ['Stop', '$021a0c000000000028#', 'Tutti i motori a zero'],
  ],
  [2500, 3500, 3638]
));
children.push(emptyPara());
children.push(para([txt('Fix critico: cmd = data[3:5].upper() in parse_data() di rosmaster_main.py — il confronto dei comandi era case-sensitive e falliva con lettere minuscole.', { italics: true, color: C.DGRAY })]));

children.push(h2('6.4 Pad di Controllo Motori — Layout 3x3'));
children.push(genericTable(
  ['Posizione', 'Pulsante', 'Azione'],
  [
    ['[0,0] Riga 1 sinistra', 'Curva sinistra', 'send_motion(0.6, 0.0, -0.4) — avanza curvando a sinistra'],
    ['[0,1] Riga 1 centro', 'Avanti', 'send_motion(1.0, 0.0, 0.0)'],
    ['[0,2] Riga 1 destra', 'Curva destra', 'send_motion(0.6, 0.0, 0.4) — avanza curvando a destra'],
    ['[1,0] Riga 2 sinistra', 'Rotazione sinistra', 'send_motion(0.0, 0.0, -1.0)'],
    ['[1,1] Riga 2 centro', 'Stop', 'send_stop()'],
    ['[1,2] Riga 2 destra', 'Rotazione destra', 'send_motion(0.0, 0.0, 1.0)'],
    ['[2,1] Riga 3 centro', 'Indietro', 'send_motion(-1.0, 0.0, 0.0)'],
  ],
  [2000, 2500, 5138]
));

// ─── SEZ 7 — CAMERA ───────────────────────────────────────────────────────────
children.push(pageBreak());
children.push(h1('7. Camera — Pipeline Colore (Consolidata v2.1)'));
children.push(para([txt('La pipeline colore è stata consolidata in v2.1. La camera OV5647 tramite picamera2 produce frame in formato RGB888 nativo. Tutte le conversioni intermedie sono state rimosse per evitare inversione dei canali R e B.')]));
children.push(emptyPara());

children.push(genericTable(
  ['Componente', 'Comportamento'],
  [
    ['picamera2 / get_frame()', 'Restituisce frame RGB888 nativo — NESSUNA conversione cvtColor'],
    ['thread_camera / g_latest_frame', 'Contiene frame RGB nativo'],
    ['mode_handle() / stream MJPEG', 'NESSUNA conversione — RGB → cv.imencode → MJPEG → Kivy colorfmt=rgb'],
    ['/capture_still endpoint', 'Frame RGB → cv.imencode JPEG qualità 95 → download su client'],
    ['camera_params.json', 'SOLO profilo streaming (profilo vision rimosso in v2.1)'],
    ['Profilo streaming', 'ColourGains(1.3,1.4) Sharpness=2.0 Contrast=1.1 Brightness=0.0 Saturation=0.8'],
  ],
  [3500, 6138]
));
children.push(emptyPara());
children.push(noteBox('ATTENZIONE: NON aggiungere conversioni cvtColor intermediate. Il frame è RGB in tutto il pipeline.'));

children.push(h2('7.1 Endpoint HTTP (porta 6500)'));
children.push(genericTable(
  ['Endpoint', 'Metodo', 'Risposta'],
  [
    ['/video_feed', 'GET', 'Stream MJPEG 31 FPS 640x480'],
    ['/capture_still', 'GET', 'File JPEG qualità 95 — nome: still_YYYYMMDD_HHMMSS.jpg'],
  ],
  [2500, 1500, 5638]
));

// ─── SEZ 8 — SENSORI E ROS2 ───────────────────────────────────────────────────
children.push(h1('8. Sensori e Stack ROS2'));

children.push(h2('8.1 Obstacle Avoidance — TOF400C VL53L1X'));
children.push(para([txt('Il sistema di obstacle avoidance primario è basato su 3 sensori TOF400C VL53L1X gestiti via multiplexer TCA9548A. La visione artificiale OpenCV è stata abbandonata in v2.1. Il RPLIDAR A1M8 rimane come sensore secondario per ostacoli alti e SLAM.')]));
children.push(emptyPara());

children.push(genericTable(
  ['Sensore', 'Posizione', 'Canale TCA9548A', 'Stato'],
  [
    ['TOF400C VL53L1X #1', 'Frontale 0°', 'CH2', '✅ Verificato (0x29)'],
    ['TOF400C VL53L1X #2', 'Sinistra 30°', 'CH3', '✅ Verificato (0x29)'],
    ['TOF400C VL53L1X #3', 'Destra 30°', 'CH4', '✅ Verificato (0x29) — sensore originale sostituito con scorta'],
    ['TOF400C VL53L1X #4', 'Spare', '—', 'Non collegato'],
  ],
  [2500, 2000, 2000, 3138]
));
children.push(emptyPara());
children.push(genericTable(
  ['Soglia', 'Azione'],
  [
    ['50cm', 'Rallentamento velocità robot'],
    ['40cm', 'Stop + rotazione pivot'],
  ],
  [3000, 6638]
));
children.push(emptyPara());
children.push(para([txt('Libreria: adafruit-circuitpython-vl53l1x v1.2.9. Approccio I2C: smbus2 per switching TCA9548A + busio.I2C per VL53L1X.')]));

children.push(h2('8.2 Sensori Ambientali — Architettura'));
children.push(genericTable(
  ['Sensore', 'Hardware', 'Stato'],
  [
    ['Temperatura / Umidità', 'DHT-11 — GPIO diretto RPi', 'Hardware disponibile — da integrare'],
    ['Rilevamento fiamma / fumo', 'OpenCV su camera OV5647', 'Da implementare — Fase 6'],
    ['Microfono / audio', 'Microfono USB', 'Da acquistare — futuro'],
    ['Gas / qualità aria', 'MQ-2 o MQ-135 + ADS1115 I2C ADC', 'Da acquistare — futuro'],
  ],
  [3000, 3000, 3638]
));
children.push(emptyPara());
children.push(genericTable(
  ['Topic MQTT', 'Payload', 'Produttore'],
  [
    ['apss/sensors/env', 'JSON: temperature, humidity, timestamp', 'Nodo ROS2 dht_node (RPi GPIO)'],
    ['apss/sensors/flame', 'JSON: detected (bool), confidence, timestamp', 'Nodo ROS2 flame_detector (OpenCV)'],
    ['apss/sensors/audio', 'JSON: level_db, event_type, timestamp', 'Nodo ROS2 audio_node (USB mic)'],
    ['apss/sensors/gas', 'JSON: ppm, gas_type, alert (bool), timestamp', 'Nodo ROS2 gas_node (ADS1115 I2C)'],
  ],
  [3000, 3000, 3638]
));

children.push(h2('8.3 Stack ROS2 — Nodi e Topic'));
children.push(genericTable(
  ['Nodo', 'Funzione', 'Stato'],
  [
    ['rplidar_node', 'Pubblica /scan (LaserScan) ~7.7Hz', 'Operativo'],
    ['robot_state_publisher', 'Pubblica TF da URDF', 'Operativo'],
    ['slam_toolbox', 'Mapping SLAM — /map topic', 'Operativo'],
    ['oled_node.py', 'Display SSD1306 — subscriber /battery (BatteryState) + fallback INA219 diretto con watchdog 5s', 'Operativo'],
    ['battery_node.py v2.0', 'Monitor INA219 — pubblica /battery (BatteryState LiFePO4 coulomb counting) + /battery/stats ogni 2s', 'Operativo'],
    ['tof_node.py', 'Legge TCA9548A CH2/CH3/CH4 — pubblica /tof/front|left|right (sensor_msgs/Range)', 'Pianificato'],
    ['avoidance_node.py', 'Subscribe /tof/* — pubblica /cmd_vel — soglie 50/40cm', 'Pianificato'],
    ['alarm_node.py', 'Subscribe /battery — allarme acustico + display OLED a soglie LOW/CRITICAL', 'Pianificato'],
  ],
  [2800, 4200, 2638]
));
children.push(emptyPara());

children.push(genericTable(
  ['Topic', 'Tipo', 'Produttore'],
  [
    ['/scan', 'sensor_msgs/LaserScan', 'rplidar_node'],
    ['/odom', 'nav_msgs/Odometry', 'thread_odom (rosmaster_main.py)'],
    ['/battery', 'sensor_msgs/BatteryState', 'battery_node v2.0'],
    ['/battery/stats', 'apss_ros2_pkg/BatteryStats', 'battery_node'],
    ['/tof/front /tof/left /tof/right', 'sensor_msgs/Range', 'tof_node (pianificato)'],
    ['/cmd_vel', 'geometry_msgs/Twist', 'avoidance_node / nav2 (pianificato)'],
    ['/apss/alarm', 'std_msgs/String', 'alarm_node (pianificato)'],
  ],
  [3000, 3000, 3638]
));

// ─── SEZ 9 — FIRMWARE ESP32 ───────────────────────────────────────────────────
children.push(pageBreak());
children.push(h1('9. Firmware ESP32 — Docking Station'));
children.push(para([txt('Il firmware MicroPython per l\'ESP32 della docking station è operativo in versione v2.1 (Maggio 2026). Gestisce monitoraggio INA219, relay di ricarica automatico, microswitch di docking e dashboard web. Documentazione completa: docs/doc_firmware.md nel repository APSS.')]));
children.push(emptyPara());

children.push(genericTable(
  ['File', 'Funzione'],
  [
    ['boot.py', 'Relay GPIO5=HIGH (aperto) come prima istruzione — sicurezza fault software. CPU 240MHz. WebREPL start (ws://192.168.1.193:8266)'],
    ['config.json', 'WiFi, pin GPIO, soglie INA219, parametri ricarica START/STOP reference, debounce microswitch 2000ms'],
    ['ina219.py', 'Driver I2C INA219 — lettura V/A/W — convenzione corrente verificata fisicamente'],
    ['main.py', 'Webserver HTTP dashboard, loop sensori 2s, IRQ microswitch con debounce 2000ms, relay automatico, watchdog CAL INA219, sync NTP pool.ntp.org'],
  ],
  [2000, 7638]
));
children.push(emptyPara());

children.push(genericTable(
  ['Funzionalità', 'Dettaglio'],
  [
    ['Webserver dashboard', 'http://192.168.1.193 — V/I/W in tempo reale, log eventi con timestamp, controllo relay, scan I2C'],
    ['NTP sync', 'pool.ntp.org — data/ora reale nel log — resync ogni ora'],
    ['INA219 polling', 'Ogni 2 secondi — tensione, corrente, potenza'],
    ['Relay automatico', 'Si chiude automaticamente se microswitch=1 (agganciato) e rete presente — senza intervento manuale'],
    ['Microswitch NC', 'IRQ su GPIO18 con debounce 2000ms — sostituisce reed switch (comportamento erratico verificato)'],
    ['Blackout detection', 'GPIO34 — partitore R1=47kΩ/R2=10kΩ — V=3.51V con rete presente'],
    ['Relay ricarica', 'CH1 GPIO5 — LOW=chiuso=ricarica abilitata, HIGH=aperto=bloccata'],
    ['Watchdog CAL INA219', 'Se V>12V e A=0 → reinizializza registro CAL azzerato da reset a caldo'],
    ['Convenzione corrente INA219', 'Positiva = ricarica attiva (XHM603 eroga verso batteria), Negativa = flusso inverso (batteria alimenta XHM603)'],
    ['Comandi REPL', 'r1() relay ON, r0() relay OFF, stato_txt() stato seriale'],
  ],
  [3000, 6638]
));

children.push(h2('9.1 Fix Applicati in v2.1 rispetto a v2.0'));
children.push(genericTable(
  ['Fix', 'Problema risolto'],
  [
    ['Debounce IRQ 2000ms su GPIO18', 'Spike dalla chiusura relay XHM603 interpretati come sgancio → relay ESP32 aperto → ricarica interrotta erroneamente'],
    ['Relay automatico nel loop 2s', 'Relay sempre aperto al boot richiedeva intervento manuale da webapp ad ogni avvio'],
    ['Watchdog CAL INA219', 'Reset a caldo ESP32 azzerava registro CAL → corrente legge 0A con tensione corretta'],
    ['config.json aggiornato LiFePO4', 'max_expected_amps 3.0→2.0, soglie tensione aggiornate per LiFePO4, sezione ricarica aggiunta con valori START/STOP di riferimento'],
    ['Branding dashboard', '"Docking Station — Rosmaster R2" → "Docking Station — APSS"'],
  ],
  [3500, 6138]
));

children.push(h2('9.2 Roadmap Firmware v2.2'));
[
  'relay_chiudi() e relay_apri() devono loggare automaticamente V/A/W INA219 al momento esatto di avvio e stop ricarica',
  'Installazione microswitch meccanico (attualmente chiuso con scotch, contatto aperto) sul fronte della docking station, al centro tra le due barre di rame che coincidono con i pogo pin (attivi) sul paraurti del robot',
  'Aggiornare webapp docking: sostituire tutti i riferimenti a \'reed\' con \'microswitch\'',
].forEach(b => children.push(bullet(b)));

// ─── SEZ 10 — CONFIG SOFTWARE RPi ─────────────────────────────────────────────
children.push(h1('10. Configurazione Software — Raspberry Pi'));
children.push(genericTable(
  ['Parametro', 'Valore'],
  [
    ['Sistema Operativo', 'Ubuntu 22.04.5 LTS (jammy) — aarch64'],
    ['Python', '3.10.12'],
    ['ROS2 Distro', 'Humble Hawksbill — ~290 package in hold'],
    ['Accesso remoto', 'NoMachine (sessione grafica remota) + SSH'],
    ['Broker MQTT', 'Mosquitto (installato su Raspberry Pi)'],
    ['Hostname Raspberry Pi', 'hawk — IP 192.168.1.158'],
    ['Hostname VM sviluppo', 'gp68-vmware — IP 192.168.1.80'],
    ['Porta TCP controllo', '6000'],
    ['Porta HTTP stream/still', '6500 — /video_feed + /capture_still'],
    ['rosmaster_main.py', 'V2.3.3 — 1115 righe'],
  ],
  [4000, 5638]
));

children.push(h2('10.1 Package Hold ROS2'));
children.push(para([txt('Entrambi i sistemi (hawk e gp68-vmware) sono tenuti a versioni allineate di ROS2 Humble con circa 290-292 package in hold per garantire la stabilità del sistema. Per sbloccare gli aggiornamenti quando necessario:')]));
children.push(emptyPara());
children.push(code('dpkg -l | grep "^ii  ros-humble-" | awk \'{print $2}\' | xargs sudo apt-mark unhold'));
children.push(emptyPara());
children.push(para([txt('Eseguire solo quando necessario — il hold garantisce stabilità del sistema di produzione.', { italics: true, color: C.DGRAY })]));

children.push(h2('10.2 USB Device Naming — Regole udev (Maggio 2026)'));
children.push(para([txt('La scheda Yahboom (CH340 1a86:7523) e il RPLIDAR A1M8 (CP2102 10c4:ea60) sono entrambi USB. L\'ordine ttyUSB0/ttyUSB1 assegnato al boot non è deterministico. Regole udev creano symlink stabili:')]));
children.push(emptyPara());
children.push(code('File: /etc/udev/rules.d/99-apss-usb.rules'));
children.push(code('SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="yahboom"'));
children.push(code('SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="rplidar"'));
children.push(emptyPara());
children.push(genericTable(
  ['Symlink', 'Dispositivo', 'Usato da'],
  [
    ['/dev/yahboom', 'CH340 Yahboom — ttyUSB0 o ttyUSB1', 'Rosmaster_Lib (patchato riga 20)'],
    ['/dev/rplidar', 'CP2102 RPLIDAR — ttyUSB0 o ttyUSB1', 'rplidar_ros (launch file)'],
  ],
  [2500, 3500, 3638]
));
children.push(emptyPara());
children.push(noteBox('Patch Rosmaster_Lib: la libreria ha /dev/ttyUSB0 hardcoded a riga 20. Patch applicata: serial.Serial(\'/dev/yahboom\', 115200). Va RIAPPLICATA se la libreria viene reinstallata via apt/pip. Backup in Rosmaster_Lib.py.bak-APSS.'));

children.push(h2('10.3 Ordine di Avvio Obbligatorio'));
children.push(genericTable(
  ['Step', 'Comando'],
  [
    ['1 — Pi Terminale 1', 'python3 ~/Workspaces/rosmaster_project/rosmaster_main.py'],
    ['2 — Pi Terminale 2 (dopo [ODOM] avviato)', 'ros2 launch apss_ros2_pkg apss_lidar.launch.py'],
    ['3 — Pi Terminale 3 (opzionale)', 'ros2 run apss_ros2_pkg battery_node.py'],
    ['4 — VM App Kivy (opzionale)', 'python3 ~/Workspaces/rosmaster_project/rosmaster_kivy/main.py'],
  ],
  [3500, 6138]
));
children.push(emptyPara());
children.push(para([txt('ATTENZIONE: rosmaster_main.py deve essere avviato PRIMA del launch file ROS2.', { bold: true, color: C.ORANGE })]));

// ─── SEZ 11 — ROADMAP ─────────────────────────────────────────────────────────
children.push(pageBreak());
children.push(h1('11. Stato Attuale e Roadmap di Sviluppo'));
children.push(genericTable(
  ['#', 'Fase', 'Stato'],
  [
    ['1', 'Specifiche e progettazione', '✅ Completa'],
    ['2', 'Circuito di ricarica XL4016 + XHM603 — LiFePO4 definitivo', '✅ Completa — v2.4'],
    ['3', 'Firmware ESP32 MicroPython v2.1', '✅ Completa — relay automatico, debounce, watchdog CAL'],
    ['4', 'App Kivy — controllo motori + stream video + pan/tilt', '✅ Completa'],
    ['5', 'RPLIDAR A1M8 + ROS2 + slam_toolbox', '✅ Completo'],
    ['6', 'Display OLED SSD1306 — oled_node.py', '✅ Completo'],
    ['7', 'Odometria encoder in rosmaster_main.py', '✅ Completa — ENCODER_CPR=822'],
    ['8', 'Camera OV5647 IR-cut — pipeline colore RGB consolidata', '✅ Completa — v2.1'],
    ['9', 'Rimozione OpenCV obstacle avoidance — pulizia codebase', '✅ Completa — v2.1'],
    ['10', 'Endpoint /capture_still — foto qualità still', '✅ Completo — v2.1 — testato'],
    ['11', 'INA219 robot + battery_node.py v2.0 + coulomb counting LiFePO4', '✅ Completo — v2.4'],
    ['12', 'TOF400C VL53L1X — tutti e 3 verificati OK via TCA9548A', '✅ Completo — v2.2'],
    ['13', 'Build app Kivy per Android (Buildozer) — APK debug 2.1', '✅ Testato Samsung S23 Ultra'],
    ['14', 'Batteria LiFePO4 ECO-WORTHY + ricalibrazione circuito + ciclo verificato', '✅ Completa — v2.4'],
    ['15', 'USB device naming udev + patch Rosmaster_Lib', '✅ Completo — v2.4'],
    ['16', 'tof_node.py + avoidance_node.py + /cmd_vel subscriber', '⏳ Pianificato — prossimo step'],
    ['17', 'alarm_node.py — allarme batteria acustico + OLED', '⏳ Pianificato'],
    ['18', 'Mappatura SLAM appartamento', '⏳ Pianificata'],
    ['19', 'Nav2 navigazione autonoma', '⏳ Pianificata'],
    ['20', 'Pattugliamento autonomo con waypoint', '⏳ Pianificata — Fase 5'],
    ['21', 'Docking autonomo ArUco', '⏳ Pianificata — Fase 7'],
    ['22', 'Sensori ambientali (DHT-11, audio, gas)', '⏳ Pianificata — Fase 8'],
  ],
  [600, 5500, 3538]
));

children.push(h2('11.1 Sviluppo Futuro — Architettura Hardware Indipendente'));
children.push(para([txt('L\'attuale implementazione APSS utilizza la scheda espansione Yahboom Rosmaster V3.0 come layer di controllo motori e servo. Questa scelta, ottimale per lo sviluppo rapido, presenta alcune limitazioni a lungo termine:')]));
children.push(emptyPara());
[
  'Il firmware STM32 sulla scheda Yahboom non è modificabile liberamente',
  'La cinematica Mecanum interna alla scheda non è compatibile con il cablaggio fisico del robot (richiede workaround con cinematica custom)',
  'Le specifiche del protocollo TCP proprietario Yahboom sono soggette a cambiamenti',
  'La disponibilità futura dei componenti dipende dal costruttore',
].forEach(b => children.push(bullet(b)));
children.push(emptyPara());
children.push(para([txt('Una architettura futura completamente indipendente potrebbe sostituire la scheda Yahboom con componenti open hardware standard:')]));
children.push(emptyPara());
children.push(genericTable(
  ['Componente attuale (Yahboom)', 'Sostituto open hardware', 'Vantaggio'],
  [
    ['Rosmaster Expansion Board V3.0 (STM32)', 'ESP32 DevKit + firmware MicroPython/ROS2', 'Firmware completamente personalizzabile'],
    ['Driver motori integrati sulla scheda', 'Driver L298N o TB6612FNG dedicati', 'Componenti standard reperibili ovunque'],
    ['Controller servo PWM integrato', 'PCA9685 I2C (16 canali PWM)', 'Espandibile, interfaccia I2C standard'],
    ['IMU MPU9250 su scheda', 'IMU MPU6050 o ICM42688 standalone', 'Flessibilità di posizionamento'],
    ['Protocollo TCP proprietario Yahboom', 'Protocollo ROS2 standard (/cmd_vel, /joint_states)', 'Compatibile con tutto l\'ecosistema ROS2'],
  ],
  [3000, 3000, 3638]
));
children.push(emptyPara());
children.push(para([txt('Con questa architettura il sistema APSS diventerebbe completamente open hardware, con il solo Raspberry Pi come elaboratore e componenti standard acquistabili ovunque.')]));

// ─── FOOTER ───────────────────────────────────────────────────────────────────
children.push(emptyPara());
children.push(new Paragraph({
  children: [txt('Documento v2.5 — Maggio 2026 — GPwebdesign — Gennaro Puzio — Uso interno', { size: 16, color: C.DGRAY, italics: true })],
  alignment: AlignmentType.CENTER,
  spacing: { before: 240, after: 80 },
  border: { top: { style: BorderStyle.SINGLE, size: 4, color: C.LBLUE, space: 4 } },
}));

// ══════════════════════════════════════════════════════════════════════════════
// BUILD DOCUMENT
// ══════════════════════════════════════════════════════════════════════════════
const doc = new Document({
  numbering: {
    config: [{
      reference: 'bullets',
      levels: [{
        level: 0,
        format: LevelFormat.BULLET,
        text: '•',
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } }
      }, {
        level: 1,
        format: LevelFormat.BULLET,
        text: '◦',
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 1080, hanging: 360 } } }
      }]
    }]
  },
  styles: {
    default: {
      document: { run: { font: FONT, size: 20 } }
    },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 28, bold: true, font: FONT, color: C.LBLUE },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 22, bold: true, font: FONT, color: C.HEADER },
        paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 20, bold: true, font: FONT, color: C.DGRAY },
        paragraph: { spacing: { before: 120, after: 60 }, outlineLevel: 2 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_W, height: 16838 },
        margin: MARGINS,
      }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          children: [
            txt('APSS — Documentazione Tecnica v2.5', { size: 16, color: C.DGRAY, italics: true }),
            new TextRun({ text: '\t', font: FONT }),
            txt('GPwebdesign — Uso interno', { size: 16, color: C.DGRAY, italics: true }),
          ],
          tabStops: [{ type: 'right', position: CONTENT_W }],
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.LBLUE, space: 4 } },
          spacing: { before: 0, after: 120 },
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          children: [
            txt('Confidenziale — Uso interno GPwebdesign', { size: 16, color: C.DGRAY }),
            new TextRun({ text: '\t\tv2.5 — Maggio 2026', font: FONT, size: 16, color: C.DGRAY, italics: true }),
          ],
          tabStops: [{ type: 'right', position: CONTENT_W }],
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: C.LBLUE, space: 4 } },
          spacing: { before: 120, after: 0 },
        })]
      })
    },
    children
  }]
});

Packer.toBuffer(doc).then(buffer => {
  const outPath = new URL('../APSS_Documentazione_Tecnica_v2_5.docx', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
  fs.writeFileSync(outPath, buffer);
  console.log('Done:', outPath);
});
