# Profile: mrds_nv

Source: `data/raw/mrds_nv.csv` (sha256 `1d83773132f0`)
Rows: 15408  Columns: 46  Exact duplicate rows: 0
Candidate keys: [['dep_id'], ['url']]

| field | dtype | nulls | unique | notes |
|---|---|---|---|---|
| dep_id | int64 | 0.0% | 15408 | min 1.00081e+07, median 1.01496e+07, max 6.00017e+07 |
| url | str | 0.0% | 15408 | top: https://mrdata.usgs.gov/mrds/show-mrds.php?dep_id=10037553(1), https://mrdata.usgs.gov/mrds/show-mrds.php?dep_id=10037726(1), https://mrdata.usgs.gov/mrds/show-mrds.php?dep_id=10042519(1) |
| mrds_id | str | 48.4% | 6430 | top: M032077(5), W002900(5), M060274(4) |
| mas_id | float64 | 41.3% | 9026 | min 3.00231e+08, median 3.20151e+08, max 3.251e+08 |
| site_name | str | 0.0% | 11420 | top: Unnamed Prospect(209), Unknown Prospect(90), Unnamed Shaft(60) |
| latitude | float64 | 0.0% | 12673 | min 35.1261, median 39.307, max 41.9849 |
| longitude | float64 | 0.0% | 13016 | min -120, median -117.247, max -114.044; 15408 negative |
| region | float64 | 100.0% | 0 |  |
| country | str | 0.0% | 1 | top: United States(15408) |
| state | str | 0.0% | 1 | top: Nevada(15408) |
| county | str | 0.0% | 25 | top: Nye(2042), Elko(1659), Pershing(1629) |
| com_type | str | 0.9% | 3 | top: M(12347), N(2166), B(756) |
| commod1 | str | 4.3% | 486 | top: Gold(4180), Silver(1450), Copper(947) |
| commod2 | str | 88.1% | 299 | top: Silver(450), Gold(212), Copper(107) |
| commod3 | str | 59.6% | 1314 | top: Silver(1338), Gold(408), Copper(198) |
| oper_type | str | 0.0% | 11 | top: Unknown(7734), Surface(2994), Underground(2937) |
| dep_type | str | 83.1% | 235 | top: Vein(1459), Replacement(184), Placer(158) |
| prod_size | str | 58.6% | 6 | CENSORED: {'lt_prefixed': 0, 'markers': 64}; top: S(3009), N(2788), M(225) |
| dev_stat | str | 0.0% | 6 | top: Past Producer(6743), Occurrence(4135), Prospect(2461) |
| ore | str | 73.5% | 1253 | top: Gold(538), Scheelite(288), Cinnabar(240) |
| gangue | str | 82.8% | 882 | top: Quartz(568), Calcite, Quartz(138), Pyrite(120) |
| other_matl | str | 96.8% | 316 | top: Pyrite(52), Barite(26), Galena(12) |
| orebody_fm | str | 79.6% | 641 | top: TABULAR(1393), IRREGULAR(272), BLANKET(151) |
| work_type | str | 91.0% | 6 | top: Underground(715), Surface/Underground(436), Surface(189) |
| model | str | 83.8% | 81 | top: 150: Epithermal vein, Comstock(385), 85: Polymetallic veins(365), 273: Low-sulfide Au-quartz vein(261) |
| alteration | str | 85.5% | 1374 | top: Silicification(298), Oxidation(141), Sericitization(21) |
| conc_proc | str | 91.2% | 615 | top: Oxidation(177), Hydrothermal(115), Replacement(105) |
| names | str | 59.4% | 5684 | top: Silver Occurrence(30), Sand and Gravel Pit(29), Gold Occurrence(20) |
| ore_ctrl | str | 78.9% | 2132 | top: Shear Zone(124), Fault Zone(116), No Information(111) |
| reporter | str | 0.3% | 810 | top: Western Field Operations Center (WFOC)(3112), Ridenour, James(2457), La Pointe, D.D. (Tingley, J.V.)(1028) |
| hrock_unit | str | 87.2% | 778 | top: Harmony Formation(63), Prospect Mountain Quartzite(59), Jarbidge Rhyolite(56) |
| hrock_type | str | 64.3% | 743 | top: Limestone(1006), Rhyolite(490), Andesite(282) |
| arock_unit | str | 96.6% | 258 | top: Jarbidge Rhyolite(58), Granitic Rocks(30), Sylvania Pluton(28) |
| arock_type | str | 81.3% | 275 | top: Diorite(562), Rhyolite(433), Granite(379) |
| structure | str | 83.8% | 1774 | top: Faults(118), Fault(49), Fractures, Postmineral Faults(41) |
| tectonic | str | 98.2% | 94 | top: Basin And Range(118), Mobile Belt(24), Basin & Range(11) |
| ref | str | 4.7% | 12096 | top: MILLER, 1996, MLA REPORT IN PREPARATION.(128), OBSERVATION(106), AREAS OF DEVELOPMENT INTEREST IN THAT PART OF THE TOQUIMARANGE, NEVADA, ADMINISTERED AS TOIYABE NATIONAL FOREST.(106) |
| yfp_ba | str | 99.0% | 2 | CENSORED: {'lt_prefixed': 138, 'markers': 0}; top: <(138), >(23) |
| yr_fst_prd | float64 | 90.4% | 137 | min 1036, median 1922.5, max 2005 |
| ylp_ba | str | 99.8% | 2 | CENSORED: {'lt_prefixed': 2, 'markers': 0}; top: >(27), <(2) |
| yr_lst_prd | float64 | 98.3% | 82 | min 1883, median 1980, max 2009 |
| dy_ba | str | 96.7% | 2 | CENSORED: {'lt_prefixed': 485, 'markers': 0}; top: <(485), >(26) |
| disc_yr | float64 | 85.0% | 151 | min 1820, median 1916, max 2002 |
| prod_yrs | str | 97.7% | 290 | CENSORED: {'lt_prefixed': 0, 'markers': 1}; top: TO 1943(10), TO 1940(6), TO 1941(5) |
| discr | str | 94.5% | 751 | top: Unknown(8), P. Downey(5), Horgan And D'Arcy(5) |
| score | str | 0.0% | 5 | top: D(8807), C(3133), B(2582) |
