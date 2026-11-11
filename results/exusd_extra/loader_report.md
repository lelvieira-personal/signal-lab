# bbg_exusd_bonds_extra.xlsx loader report (decisions/0068, HANDOFF task 89)

Counts, dates and labels only.

| Ticker | Index name | Daily start | Tier | CCY | Investable | Level rows before holdout | Dates dropped (no rate) | Analytics starts | Duration axis |
|---|---|---|---|---|---|---|---|---|---|
| `BEIG1T` | - | 1999-12-31 | backbone | EUR | True | 5216 | 0 | none | estimated loading (minus the real-yield loading) |
| `BEIG3T` | - | 1999-12-31 | backbone | EUR | True | 5218 | 0 | none | estimated loading (minus the real-yield loading) |
| `I08043GB` | 1-3 Year | 2003-10-09 | second | GBP | True | 4113 | 0 | INDEX_OAD_TSY 2009-05-18; INDEX_OAS_TSY 2003-10-09; INDEX_YIELD_TO_WORST 2009-05-18 | measured OAD where the week has one, estimated loading otherwise |
| `I08044GB` | 3-5 Year | 2003-10-09 | second | GBP | True | 4113 | 0 | INDEX_OAD_TSY 2004-09-07; INDEX_OAS_TSY 2003-10-09; INDEX_YIELD_TO_WORST 2004-09-07 | measured OAD where the week has one, estimated loading otherwise |
| `I08045GB` | 5-7 Year | 2003-10-09 | second | GBP | True | 4105 | 0 | INDEX_OAD_TSY 2006-09-08; INDEX_OAS_TSY 2003-10-09; INDEX_YIELD_TO_WORST 2006-09-08 | measured OAD where the week has one, estimated loading otherwise |
| `I08046GB` | 7-10 Year | 2003-10-09 | second | GBP | True | 4105 | 0 | INDEX_OAD_TSY 2015-06-12; INDEX_OAS_TSY 2003-10-09; INDEX_YIELD_TO_WORST 2015-06-12 | measured OAD where the week has one, estimated loading otherwise |
| `I08047GB` | 10-15 Year | 2003-10-09 | second | GBP | True | 4105 | 0 | INDEX_OAD_TSY 2014-09-17; INDEX_OAS_TSY 2003-10-09; INDEX_YIELD_TO_WORST 2014-09-17 | measured OAD where the week has one, estimated loading otherwise |
| `I08048GB` | 15+ Year | 2003-10-09 | second | GBP | True | 4105 | 0 | INDEX_OAD_TSY 2014-09-17; INDEX_OAS_TSY 2003-10-09; INDEX_YIELD_TO_WORST 2014-09-17 | measured OAD where the week has one, estimated loading otherwise |
| `LEATTREU` | Treasury | 1998-07-31 | backbone | EUR | False | 5427 | 2 | INDEX_OAD_TSY 2002-04-23; INDEX_OAS_TSY 2002-09-17; INDEX_YIELD_TO_WORST 2002-04-23 | none: reference series, not held |
| `LET0TREU` | 10+ Year | 1998-07-31 | backbone | EUR | True | 5427 | 2 | INDEX_OAD_TSY 2008-06-06; INDEX_OAS_TSY 2002-09-17; INDEX_YIELD_TO_WORST 2008-06-06 | measured OAD where the week has one, estimated loading otherwise |
| `LET3TREU` | 3-5 Year | 1998-07-31 | backbone | EUR | True | 5427 | 2 | INDEX_OAD_TSY 2004-09-07; INDEX_OAS_TSY 2002-09-17; INDEX_YIELD_TO_WORST 2004-09-07 | measured OAD where the week has one, estimated loading otherwise |
| `LET5TREU` | 5-7 Year | 1998-07-31 | backbone | EUR | True | 5427 | 2 | INDEX_OAD_TSY 2009-05-19; INDEX_OAS_TSY 2002-09-17; INDEX_YIELD_TO_WORST 2009-05-19 | measured OAD where the week has one, estimated loading otherwise |
| `LET7TREU` | 7-10 Year | 1998-07-31 | backbone | EUR | True | 5427 | 2 | INDEX_OAD_TSY 2009-05-19; INDEX_OAS_TSY 2002-09-17; INDEX_YIELD_TO_WORST 2009-05-19 | measured OAD where the week has one, estimated loading otherwise |
| `LSG1TRGU` | Gilts | 2003-07-31 | second | GBP | False | 4161 | 0 | INDEX_OAD_TSY 2006-03-20; INDEX_OAS_TSY 2003-07-31; INDEX_YIELD_TO_WORST 2006-03-20 | none: reference series, not held |

## The linkers

- `BEIG1T`: dates with a number in the analytics sheet: oad_tsy 0, yield_to_worst 0, oas 0
- `BEIG3T`: dates with a number in the analytics sheet: oad_tsy 0, yield_to_worst 0, oas 0

FLDS test (`linker_fields`, the `_is_number` columns only):

| Mnemonic | BEIG1T | BEIG3T |
|---|---|---|
| `INDEX_MODIFIED_DURATION` | False | False |
| `INDEX_OAD_TSY` | False | False |
| `INDEX_REAL_DURATION` | False | False |
| `INDEX_REAL_YIELD` | False | False |
| `INDEX_REAL_YIELD_TO_WORST` | False | False |
| `INDEX_YIELD_TO_WORST` | False | False |
| `MODIFIED_DURATION` | True | True |
| `Test only: no history pulled. Real-duration / real-yield fields to be confirmed via FLDS.` | None | None |
| `YLD_YTM_MID` | False | False |

- Analytics rows before the holdout: 51451; on or after: 0.
