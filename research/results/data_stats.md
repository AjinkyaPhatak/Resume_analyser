# Dataset statistics

## BiasBios

Split strategy: **official**. Gender is binary in the source data (M/F).

| Split | raw | too short | dup in split | overlaps earlier split | kept | % F | mean words | median words |
|---|---|---|---|---|---|---|---|---|
| train | 257478 | 0 | 384 | 0 | 257094 | 46.1 | 60.7 | 55 |
| dev | 39642 | 0 | 18 | 88 | 39536 | 46.1 | 60.6 | 55 |
| test | 99069 | 0 | 67 | 254 | 98748 | 46.1 | 60.7 | 55 |

### Counts per occupation and gender

| Occupation | train F | train M | dev F | dev M | test F | test M | test % F |
|---|---|---|---|---|---|---|---|
| accountant | 1341 | 2314 | 205 | 357 | 514 | 888 | 36.7 |
| architect | 1554 | 4999 | 240 | 770 | 597 | 1921 | 23.7 |
| attorney | 8079 | 13043 | 1243 | 2003 | 3088 | 5004 | 38.2 |
| chiropractor | 452 | 1248 | 69 | 194 | 175 | 476 | 26.9 |
| comedian | 384 | 1436 | 60 | 222 | 149 | 553 | 21.2 |
| composer | 594 | 3040 | 92 | 469 | 230 | 1166 | 16.5 |
| dentist | 3338 | 6113 | 514 | 939 | 1280 | 2341 | 35.3 |
| dietitian | 2380 | 183 | 367 | 29 | 914 | 71 | 92.8 |
| dj | 136 | 828 | 22 | 127 | 53 | 319 | 14.2 |
| filmmaker | 1494 | 3047 | 229 | 470 | 575 | 1169 | 33.0 |
| interior_designer | 765 | 182 | 118 | 28 | 295 | 71 | 80.6 |
| journalist | 6404 | 6525 | 985 | 1002 | 2458 | 2512 | 49.5 |
| model | 4024 | 838 | 620 | 130 | 1547 | 322 | 82.8 |
| nurse | 11181 | 1126 | 1719 | 174 | 4295 | 433 | 90.8 |
| painter | 2296 | 2725 | 353 | 420 | 885 | 1049 | 45.8 |
| paralegal | 972 | 173 | 145 | 27 | 373 | 67 | 84.8 |
| pastor | 393 | 1243 | 61 | 192 | 152 | 478 | 24.1 |
| personal_trainer | 422 | 505 | 66 | 78 | 163 | 194 | 45.7 |
| photographer | 5627 | 10125 | 862 | 1560 | 2159 | 3894 | 35.7 |
| physician | 13146 | 13470 | 2021 | 2072 | 5047 | 5183 | 49.3 |
| poet | 2234 | 2322 | 343 | 358 | 860 | 891 | 49.1 |
| professor | 34581 | 42076 | 5313 | 6464 | 13289 | 16158 | 45.1 |
| psychologist | 7407 | 4527 | 1139 | 696 | 2844 | 1740 | 62.0 |
| rapper | 88 | 823 | 14 | 127 | 34 | 317 | 9.7 |
| software_engineer | 709 | 3774 | 110 | 577 | 270 | 1446 | 15.7 |
| surgeon | 1308 | 7510 | 202 | 1156 | 504 | 2885 | 14.9 |
| teacher | 6337 | 4180 | 974 | 642 | 2432 | 1604 | 60.3 |
| yoga_teacher | 908 | 165 | 141 | 26 | 349 | 65 | 84.3 |

## Job descriptions (LinkedIn postings, arshkon, CC BY-SA 4.0)

Cleaning: {'raw': 123849, 'missing_title_or_description': 7, 'too_short': 1263, 'duplicate_description': 16253, 'kept': 106326}

Occupation map: 8003 unique titles matched; status counts {'auto': 6889, 'ambiguous': 1114}; **1114 ambiguous titles await review** in `research/data/occupation_map.csv` (excluded until reviewed). High-priority ambiguous titles (candidate occupation short of JDs): 75. Postings dropped by description requirements: {'architect': 256}. Postings mapped to an occupation: 11513.

| Occupation | SOC | postings mapped | JDs used | dev JDs | test JDs | mean JD words (used) |
|---|---|---|---|---|---|---|
| accountant | 13-2011 | 1231 | 20 | 6 | 14 | 409 |
| architect | 17-1011 | 62 | 20 | 6 | 14 | 492 |
| attorney | 23-1011 | 827 | 20 | 6 | 14 | 366 |
| chiropractor | 29-1011 | 7 | 7 | 2 | 5 | 310 |
| comedian | 27-2099 | 0 | 0 | 0 | 0 | – |
| composer | 27-2041 | 0 | 0 | 0 | 0 | – |
| dentist | 29-1021 | 105 | 20 | 6 | 14 | 335 |
| dietitian | 29-1031 | 79 | 20 | 6 | 14 | 527 |
| dj | 27-3011 | 0 | 0 | 0 | 0 | – |
| filmmaker | 27-2012 | 1 | 0 | 0 | 0 | – |
| interior_designer | 27-1025 | 57 | 20 | 6 | 14 | 471 |
| journalist | 27-3023 | 48 | 20 | 6 | 14 | 536 |
| model | 41-9012 | 1 | 0 | 0 | 0 | – |
| nurse | 29-1141 | 5473 | 20 | 6 | 14 | 570 |
| painter | 27-1013 | 0 | 0 | 0 | 0 | – |
| paralegal | 23-2011 | 397 | 20 | 6 | 14 | 304 |
| pastor | 21-2011 | 4 | 0 | 0 | 0 | – |
| personal_trainer | 39-9031 | 23 | 20 | 6 | 14 | 630 |
| photographer | 27-4021 | 14 | 14 | 4 | 10 | 330 |
| physician | 29-1229 | 580 | 20 | 6 | 14 | 475 |
| poet | 27-3043 | 0 | 0 | 0 | 0 | – |
| professor | 25-1199 | 90 | 20 | 6 | 14 | 706 |
| psychologist | 19-3033 | 97 | 20 | 6 | 14 | 619 |
| rapper | 27-2042 | 0 | 0 | 0 | 0 | – |
| software_engineer | 15-1252 | 1847 | 20 | 6 | 14 | 397 |
| surgeon | 29-1249 | 13 | 13 | 4 | 9 | 498 |
| teacher | 25-2031 | 556 | 20 | 6 | 14 | 392 |
| yoga_teacher | 39-9031 | 1 | 0 | 0 | 0 | – |

Occupations without pools (too few JDs): comedian, composer, dj, filmmaker, model, painter, pastor, poet, rapper, yoga_teacher

## Candidate pools

| Pool set | pools | rows | relevant/pool | % F (all) | % F (relevant) | graded 2 / 1 / 0 |
|---|---|---|---|---|---|---|
| dev | 100 | 10000 | 10.0 | 50.0 | 50.0 | 1000 / 1116 / 7884 |
| test | 234 | 23400 | 10.0 | 50.0 | 50.0 | 2340 / 2592 / 18468 |
