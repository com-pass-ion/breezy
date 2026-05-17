# *breezy:* 
## ~ *Ihr Meditationstrainer für die Hosentasche* ~

### Kurzbeschreibung:
  
***breezy*** ist ein eigenständiger, adaptiver Biofeedback-Meditationstrainer auf Basis eines ESP32.

https://github.com/user-attachments/assets/95bb95b5-2758-490a-abf5-11077871adc9

### Zielsetzung und Konzept

***Ziel:***

Ein stand-alone Gerät, das sich automatisch mit einem Polar-Device verbindet, EKG- und Atemsignale (Brustkorbbewegung) erfasst, diese verarbeitet und in ein weiches, hochauflösendes PWM-Lichtsignal übersetzt.

Die Nutzererfahrung steht im Vordergrund; eine App dient primär zur Datenauswertung und zur Auswahl grundlegender Funktionen.

Das Projekt dient zugleich dem vertieften Verständnis von Algorithmen, Signalverarbeitung und Embedded-Programmierung in C.


***Konzept:***

- Automatische Verbindung zu Polar-Sensoren
- Echtzeit-Signalverarbeitung für adaptives Biofeedback
- Dezente Lichtvisualisierung als Atem- und Entspannungsleitfaden
- Prototyping in Python, finale Implementierung in C auf ESP32

### Technische Umsetzung

![***Prototyp 0.0.1:***](./prototype_0.0.1/pwm_script_23_02_2026.py)

![Breezy Circuit Diagram](./circuit/prototype_circuit.svg)

- Entwicklungsboard: Unihiker Ein‑Platinen‑Computer
- Prototyp-Sprache: Python
- Fokus: Erzeugung eines möglichst weichen, hochauflösenden PWM‑Signals und Validierung grundlegender Programmierkonzepte

***Hardwarehinweise:***

- Schaltung mit hohen Widerstandswerten zur Augenschonung bei wiederholten Tests
- Kondensator wird je nach Testziel angepasst oder entfernt

### Einschränkungen 

- PWM-Aktualisierungsrate ist auf 20-30Hz beim Unihiker begrenzt
- Aktuelle Atemmodellierung basiert auf einer symmetrischen Gauß-Kurve und ist noch nicht auf Atemphasen-/pausen skalierbar.
- Der Prototyp arbeitet derzeit mit ***simulierten*** Signalen.
- Entwicklung ist momentan an den Unihiker als Board gebunden.

### Zielsetzung für nächste Projektphase:

***Ziel***

Funktionsfähiger Python-Prototyp mit simuliertem Signal und adaptiver Lichtvisualisierung.

***Nächste Schritte:*** 

- Integration echter Biofeedback-Signale (nicht simuliert)
- Verbesserung der Atemmodellierung und Skalierbarkeit auf Atemphasen und Pausen

### Kontakt und Mitwirkung

Beiträge, Feedback und Fragen sind willkommen.

