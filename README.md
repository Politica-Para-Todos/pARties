# PPT utility functions

Set of scripts to accelerate work.

## Create Google Service Account

Follow [this guide](https://www.analyticsvidhya.com/blog/2020/07/read-and-update-google-spreadsheets-with-python/). After creating the service account you need to add an API Key to it. That API key must be place in the root of the project under name `google_auth.json`. Finally, you need to add the service account email as editor to the spreadsheet, otherwise you only have read access.

Documentation to access a spreadsheet programmatically: https://docs.gspread.org/en/v5.1.1/.

# Get parties candidates

Sometimes we can extract all or part of the candidates from trusted sources. Please check file `get_candidates.py` for details.

To execute the script run:

```bash
make get_candidates
```

# Get final json

To build the json that is used to populate the database run:

```bash
# only once
cd ..
git clone git@github.com:Politica-Para-Todos/manifestos.git
cp -r ../manifestos/legislativas/20220130_legislativas manifestos
cd pARties
```

```bash
make run
```

Open [localhost:5001/all](localhost:5001/all) and store the json in your pc. You also have the `/manifestos` and `parties`.