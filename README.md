# Decision-Tree-Builder-for-Athlete-Data

Dieses Repository enthält eine Webanwendung zur Erstellung und Verwaltung von Entscheidungsbäumen, speziell für Trainer konzipiert. Entscheidungsbäume sind leistungsstarke Instrumente für datengesteuerte Entscheidungen, und diese Anwendung bietet eine intuitive Benutzeroberfläche, um Entscheidungsbäume effektiv zu erstellen, zu speichern und zu nutzen.

# Projektbeschreibung
Die Webanwendung ist darauf ausgelegt, Trainern bei der effizienten Konstruktion von Entscheidungsbäumen zu unterstützen. In diesem Kontext sind Trainer die Hauptbenutzer (Akteure) der Anwendung. Sie können die Anwendung nutzen, um Entscheidungsbäume aufzubauen, die als wertvolle Werkzeuge für die Entscheidungsfindung dienen.

Die wesentlichen Schritte für die Konstruktion eines Entscheidungsbaums durch den Trainer umfassen:

Schwellenwerte eingeben: Der Trainer muss spezifische Schwellenwertwerte eingeben, die die Entscheidungsknoten innerhalb des Entscheidungsbaums definieren. Diese Schwellenwerte beeinflussen wesentlich den Entscheidungsprozess innerhalb des Baums.
Knoten auswählen: Nach Eingabe der Schwellenwerte kann der Trainer einen bestimmten Knoten im Entscheidungsbaum auswählen, zu dem er die nächsten Knoten hinzufügen möchte. Diese Auswahl ermöglicht es dem Trainer, sich auf bestimmte Pfade im Baum zu konzentrieren und sich auf weitere Ergänzungen vorzubereiten.
TestID auswählen: Im letzten Schritt muss der Trainer eine bestimmte TestID auswählen, die den Knoten entspricht, die hinzugefügt werden sollen. Die TestID repräsentiert die Menge von Knoten, die basierend auf der Auswahl des Trainers in den Entscheidungsbaum eingefügt werden.
Alle drei oben genannten Schritte sind obligatorisch für den erfolgreichen Aufbau des Baums. Nach Abschluss des Prozesses hat der Trainer die Möglichkeit, den erstellten Entscheidungsbaum zu speichern, was die Flexibilität bietet, auf ihn zuzugreifen und ihn für zukünftige Referenzen zu nutzen.

Zusätzlich bietet die Webanwendung zwei wertvolle Funktionalitäten im Zusammenhang mit dem Entscheidungsbaum:

Anzeigen von Knoteninformationen: Der Trainer kann auf detaillierte Informationen zu bestimmten Knoten im Entscheidungsbaum zugreifen und diese anzeigen. Diese Funktion ermöglicht es dem Trainer, Einblicke in die Merkmale und Attribute einzelner Knoten zu gewinnen.
Empfehlungen: Der Trainer hat die Möglichkeit, eine Empfehlung im Zusammenhang mit dem Entscheidungsbaum zu verfassen. Alternativ kann der Trainer, falls bereits eine Empfehlung vorhanden ist, wählen, sie anzuzeigen. Empfehlungen dienen als Entscheidungshilfen für Athleten und unterstützen sie bei der Auswahl entsprechender Entscheidungen auf der Grundlage der Ergebnisse des Entscheidungsbaums.
Auf der anderen Seite der Webanwendung kann der Trainer einen umfassenden Überblick über die erstellten Entscheidungsbäume und die von ihm verfassten Empfehlungen erhalten. Diese Funktionalität erleichtert das effiziente Management und die Überprüfung der in der Vergangenheit erstellten Entscheidungsbäume.

# Datenbank und Daten
PostgreSQL wurde als Datenbank für das Projekt gewählt, da es die Möglichkeit bietet, JSON-Objekte zu speichern. Dies ermöglicht die Speicherung der Netzwerkelemente und Empfehlungen als JSON-Objekte, was die Flexibilität und Skalierbarkeit für komplexe Entscheidungsbaumstrukturen bietet. Die Datenbank enthält eine einzige Tabelle namens "store", die die Entscheidungsbaumstrukturen und zugehörigen Empfehlungen speichert. Die Daten für dieses Projekt stammen aus der API: https://inprove-sport.info/csv/getInproveDemo/hgnxjgTyrkCvdR

# Verbindung der Benutzeroberfläche mit dem Datenbank-Backend
Die Verbindung zwischen der Benutzeroberfläche und dem Datenbank-Backend umfasst die Verwendung von Callback-Funktionen im Dash-Framework, um Daten zwischen der Benutzeroberfläche und der Datenbank auszutauschen.

# Anleitung zur Ausführung
To run the decision tree, follow these steps:

Python version 3.10 is required to be installed.

For example, you can do this using conda (if you don't have conda, you can install it
here: https://docs.conda.io/en/latest/)

````bash
conda create -n decisiontree python=3.10.8
conda activate decisiontree
````

### Install dependencies

```bash
pip install -r requirements.txt
```

### Set up the postgres database

Data for the program is stored in postgres.
First docker needs to be installed (see here: https://docs.docker.com/). We use docker-compose to set up the database -
see
`docker-compose.yaml`. File is a Dockerfile that creates a local postgres database and creates a db
"postgres" with user "postgres" and password "postgres".

```bash
docker-compose up -d 
```

Then with pgadmin (https://www.pgadmin.org/download/) a Server with the postgres connection needs to be established.
Then you can create the table "store" by running the python script `table_creation.py`

If you already have a postgres instance with this db, table and user/password running,
you can skip this step.

### Run the program

To run the decision tree creation frontend do

````bash
python3 tree_creation.py
````

and to run the decision tree loading frontend do

````bash
python3 tree_loading.py
````
