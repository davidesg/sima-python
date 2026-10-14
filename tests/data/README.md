# Test data

`gas_furnace.csv` — Box and Jenkins' Series J (gas rate, CO2; 296 pairs at 9 s),
from <https://openmv.net/info/gas-furnace> (md5 4950b8ad0b048c453257747ea6e04078),
the copy in drvarma's `tests/data/tiao_box/`. Route V's test (Tiao and Box 1981, §5.2).

`flour_art/` — art's univariate models of Lütkepohl and Poskitt's flour prices
(the `lutkepohl_poskitt` example's data, logs, d = 1): Buffalo a random walk,
Minneapolis and Kansas City an AR(1). Route U in the echelon form
(`test_echelon_route_u.py`).
