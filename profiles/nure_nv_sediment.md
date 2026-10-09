# Profile: nure_nv_sediment

Source: `data/raw/nure_nv_sediment.csv` (sha256 `6fe27c3c557b`)
Rows: 27630  Columns: 145  Exact duplicate rows: 0
Candidate keys: [['rec_no']]

| field | dtype | nulls | unique | notes |
|---|---|---|---|---|
| rec_no | int64 | 0.0% | 27630 | min 5.13535e+06, median 5.14941e+06, max 5.17056e+06 |
| prime_id | str | 0.0% | 25171 | top: 20729(4), EYAG068S1(2), EYAG069S1(2) |
| replc | int64 | 0.0% | 5 | min 0, median 0, max 111 |
| samptyp | int64 | 0.0% | 14 | min 50, median 61, max 99 |
| rec_cnt | int64 | 0.0% | 2 | min 1, median 1, max 2 |
| latitude | float64 | 0.1% | 18339 | min 35.116, median 39.3256, max 41.9973 |
| longitude | float64 | 0.2% | 17718 | min -119.998, median -116.349, max -114.038; 27587 negative |
| doelab | str | 0.0% | 2 | top: SRL-W(18735), LLL(8895) |
| laslid | float64 | 100.0% | 0 |  |
| ornlid | float64 | 78.2% | 6014 | min 214585, median 274276, max 280125 |
| srlid | str | 26.3% | 18364 | top: EYAG068S1(2), EYAG069S1(2), EYAG070S1(2) |
| lllid | str | 67.8% | 8445 | mixed numeric/text: ['36316WR', '58091SD', '5184WR', '36317WR', '7432WS']; top: 20729(4), 7032(2), 9404(2) |
| site | float64 | 99.6% | 98 | min 6324, median 13499.5, max 57904 |
| state | str | 0.0% | 1 | top: NV(27630) |
| quad | str | 0.0% | 18 | top: RENO(2907), MCDERMITT(2422), KINGMAN(2128) |
| mapcode | str | 0.0% | 18 | top: NJ1101(2904), NK1108(2422), NI1103(2128) |
| fips | float64 | 0.2% | 17 | min 32001, median 32013, max 32510 |
| huc8 | float64 | 0.2% | 71 | min 1.501e+07, median 1.606e+07, max 1.80902e+07 |
| ls_map | str | 0.2% | 1840 | top: 36116NWG2(743), 36116NWF2(366), 36116NWG3(286) |
| study | str | 93.5% | 2 | top: DS25(1612), PO03(186) |
| phase | float64 | 100.0% | 0 |  |
| strbasin | float64 | 100.0% | 0 |  |
| b_lat_c | float64 | 100.0% | 0 |  |
| b_long_c | float64 | 100.0% | 0 |  |
| smpmedia | str | 0.0% | 1 | top: SEDIMENT(27630) |
| sampsrc | str | 0.0% | 5 | top: STREAM(17518), SOIL(9709), PLAYA(243) |
| sedcond | str | 36.5% | 2 | top: DRY(14418), WET(3120) |
| sizefrxn | str | 1.5% | 3 | top: -100 MESH(17840), -18/+35 MESH(7013), -18/+100 MESH(2375) |
| osamptyp | str | 84.6% | 1 | top: STREAM SEDIMENT(4258) |
| lsamptyp | str | 78.2% | 1 | top: SEDIMENT(6014) |
| ssamptyp | str | 38.0% | 7 | top: STREAM SEDIMENT ONLY(8370), SOIL(8097), STREAM SEDIMENT + WATER(273) |
| sedtreat | str | 99.3% | 1 | top: SIEVED(186) |
| sampdat | str | 14.7% | 640 | dates 1975-08-21 to 1980-09-02 |
| samphr | float64 | 100.0% | 0 |  |
| sampler | float64 | 32.2% | 51 | min 1, median 45, max 111 |
| grabs | float64 | 32.2% | 22 | min 1, median 10, max 40 |
| weather | float64 | 100.0% | 0 |  |
| airtemp | float64 | 100.0% | 0 |  |
| wtrtemp | float64 | 99.0% | 28 | min 2, median 16, max 73 |
| ph | float64 | 99.0% | 32 | min 3.8, median 8.1, max 9.4 |
| cond | float64 | 99.0% | 106 | min 20, median 160, max 900 |
| alk | float64 | 99.0% | 58 | min 0.25, median 1.6, max 5.7 |
| o_diss | float64 | 100.0% | 0 |  |
| scin | float64 | 32.7% | 144 | min 0, median 49, max 280 |
| orgn_pct | float64 | 100.0% | 0 |  |
| sampodor | str | 86.7% | 2 | top: NONE(3671), H2S(1) |
| smpcolr | float64 | 100.0% | 0 |  |
| sgeounit | str | 32.2% | 252 | top: QTRN(9774), UNKN(3071), TRTR(2244) |
| rocktyp | str | 38.0% | 10 | top: UNCONSOLIDATED VALLEY FILL(7627), OTHER(4656), VOLCANIC - FELSIC(2286) |
| rockclr | float64 | 100.0% | 0 |  |
| sedtype | str | 38.0% | 5 | top: SAND(9299), PEBBLES & COARSER(3930), SILT & CLAY(3458) |
| sedcolr | float64 | 100.0% | 0 |  |
| strwdth | float64 | 100.0% | 0 |  |
| strwdthc | str | 38.0% | 7 | CENSORED: {'lt_prefixed': 6, 'markers': 0}; top: DRY(16830), 2 - 4 FT(97), 1 - 2 FT(94) |
| strdpth | float64 | 100.0% | 0 |  |
| strdpthc | str | 38.0% | 6 | CENSORED: {'lt_prefixed': 101, 'markers': 0}; top: DRY(16851), 0.5 - 1 FT(134), < 0.5 FT(101) |
| wtrlevel | str | 38.0% | 4 | top: DRY(16838), NORMAL(223), LOW(38) |
| strflow | float64 | 100.0% | 0 |  |
| strflowc | str | 84.4% | 5 | top: STAGNANT(4263), MODERATE(21), FAST(10) |
| wtrcolr | float64 | 100.0% | 0 |  |
| strchanl | float64 | 100.0% | 0 |  |
| vegtype | str | 38.0% | 6 | top: DESERT SCRUB(14352), FOREST(1795), GRASS OR PASTURE(709) |
| vegdens | str | 38.0% | 3 | top: MODERATE(9875), SPARSE(5521), DENSE(1727) |
| relief | str | 38.0% | 4 | top: FLAT (0 - 3 M)(7356), LOW (3 - 15 M)(4819), GENTLE (15 - 60 M)(2834) |
| contamc | str | 14.1% | 70 | top: GRAZING(10984), NONE(8282), SEWAGE(1353) |
| specms | float64 | 100.0% | 0 |  |
| tapedata | float64 | 100.0% | 0 |  |
| analdate | str | 70.8% | 82 | dates 1979-09-10 to 1981-03-23 |
| batch_es | float64 | 100.0% | 0 |  |
| asbatch | float64 | 100.0% | 0 |  |
| clbatch | float64 | 100.0% | 0 |  |
| po4batch | float64 | 100.0% | 0 |  |
| snbatch | float64 | 100.0% | 0 |  |
| hgbatch | float64 | 100.0% | 0 |  |
| ubatch_dn | float64 | 84.8% | 15 | min 5209, median 5214, max 5260 |
| ubatch_fl | float64 | 93.8% | 14 | min 5183, median 5203, max 5208 |
| ubatch_ms | float64 | 100.0% | 0 |  |
| ubatch_xx | float64 | 100.0% | 0 |  |
| u_xx_mthd | str | 77.9% | 1 | top: SR3-XU(6117) |
| u_xx_ppm | float64 | 77.9% | 166 | min -0.2, median 0.9, max 92.1; 101 negative |
| u_dn_ppm | float64 | 11.1% | 1117 | min -14.2, median 3.1, max 248.22; 14 negative |
| u_fl_ppm | float64 | 93.8% | 345 | min -0.25, median 2.59, max 336; 1 negative |
| u_ms_ppm | float64 | 100.0% | 0 |  |
| u_na_ppm | float64 | 74.9% | 4080 | min -2, median 3.3175, max 260.1; 947 negative |
| ag_ppm | float64 | 31.0% | 208 | min -500, median -2, max 683; 12787 negative |
| al_pct | float64 | 6.6% | 9323 | min -0.05, median 6.016, max 17.41; 353 negative |
| as_ppm | float64 | 52.8% | 3122 | min -3, median 4, max 827; 3318 negative |
| au_ppm | float64 | 66.9% | 239 | min -0.01, median -0.01, max 30.613; 8788 negative |
| b_ppm | float64 | 78.2% | 160 | min -10, median 24, max 2238; 331 negative |
| ba_ppm | float64 | 30.3% | 4249 | min -100, median 583.9, max 117100; 842 negative |
| be_ppm | float64 | 56.1% | 29 | min -1, median 2, max 36; 82 negative |
| bi_ppm | float64 | 100.0% | 0 |  |
| br_ppm | float64 | 74.7% | 1467 | min -5, median -5, max 516.2; 5393 negative |
| ca_pct | float64 | 30.4% | 4225 | min -2, median 1.8, max 41.87; 3016 negative |
| cd_ppm | float64 | 100.0% | 0 |  |
| ce_ppm | float64 | 8.9% | 5057 | min -63, median 58, max 1704; 1450 negative |
| cl_ppm | float64 | 74.9% | 1198 | min -50, median -50, max 75570; 5490 negative |
| co_ppm | float64 | 30.4% | 3360 | min -5, median 6, max 2485; 4459 negative |
| cr_ppm | float64 | 30.3% | 3746 | min -30, median 31, max 13297; 2377 negative |
| cs_ppm | float64 | 74.2% | 3349 | min -30, median 3.939, max 234.6; 2821 negative |
| cu_ppm | float64 | 56.1% | 242 | min -2, median 15, max 11000; 19 negative |
| dy_ppm | float64 | 38.9% | 4517 | min -15, median 1.9, max 85.9; 6985 negative |
| eu_ppm | float64 | 34.2% | 3636 | min -15.5, median 0.5018, max 183300; 8158 negative |
| f_ppm | float64 | 100.0% | 0 |  |
| fe_pct | float64 | 6.8% | 8584 | min -52.1, median 2.37, max 33.54; 467 negative |
| hf_ppm | float64 | 11.4% | 3940 | min -15, median 4, max 147; 7618 negative |
| hg_ppm | float64 | 74.9% | 698 | min -500, median -500, max 40620; 6224 negative |
| k_pct | float64 | 30.9% | 3862 | min -0.2, median 1.8, max 46.09; 973 negative |
| la_ppm | float64 | 14.5% | 4519 | min -7093, median 31, max 12313; 2184 negative |
| li_ppm | float64 | 56.1% | 151 | min -5, median 22, max 581; 234 negative |
| lu_ppm | float64 | 49.1% | 3720 | min -13000, median 0.3, max 5.7; 2928 negative |
| mg_pct | float64 | 30.9% | 4888 | min -0.906, median 0.7, max 16.82; 467 negative |
| mn_ppm | float64 | 7.5% | 5757 | min -114, median 538, max 295900; 367 negative |
| mo_ppm | float64 | 55.4% | 218 | min -4, median -2, max 161; 9733 negative |
| na_pct | float64 | 6.2% | 6815 | min -0.1, median 1.442, max 35.9066; 207 negative |
| nb_ppm | float64 | 56.1% | 67 | min -5, median 11, max 149; 1821 negative |
| ni_ppm | float64 | 56.1% | 107 | min -5, median 12, max 9195; 664 negative |
| p_ppm | float64 | 56.1% | 1262 | min -20, median 666, max 18281; 20 negative |
| pb_ppm | float64 | 56.1% | 193 | min -10, median 15, max 89867; 2804 negative |
| pt_ppm | float64 | 100.0% | 0 |  |
| rb_ppm | float64 | 74.2% | 2117 | min -150, median 80.46, max 700.4; 2936 negative |
| sb_ppm | float64 | 74.2% | 3693 | min -0.5, median 1.284, max 1800; 2334 negative |
| sc_ppm | float64 | 6.0% | 5018 | min -1, median 5.9, max 58.15; 435 negative |
| se_ppm | float64 | 77.8% | 9 | min -1, median -1, max 9; 4667 negative |
| sm_ppm | float64 | 34.5% | 3437 | min -182, median 4, max 388; 4521 negative |
| sn_ppm | float64 | 77.8% | 31 | min -5, median -5, max 255; 3487 negative |
| sr_ppm | float64 | 40.8% | 2567 | min -50, median 156, max 170300; 6066 negative |
| ta_ppm | float64 | 74.2% | 1354 | min -3, median -3, max 32.71; 5612 negative |
| tb_ppm | float64 | 74.2% | 505 | min -20, median -20, max 5.823; 6588 negative |
| th_ppm | float64 | 7.1% | 4038 | min -49, median 10, max 6326; 1362 negative |
| ti_ppm | float64 | 10.5% | 6842 | min -1923, median 2869.5, max 54993; 2260 negative |
| v_ppm | float64 | 6.9% | 4912 | min -32, median 60, max 3957; 666 negative |
| w_ppm | float64 | 52.6% | 270 | min -30, median -30, max 732.3; 12300 negative |
| y_ppm | float64 | 56.1% | 62 | min -5, median 11, max 148; 2290 negative |
| yb_ppm | float64 | 45.4% | 3340 | min -957, median 1.7, max 103.4; 5199 negative |
| zn_ppm | float64 | 30.4% | 1505 | min -200, median 45, max 45855; 5680 negative |
| zr_ppm | float64 | 77.6% | 424 | min -2, median 66, max 2370; 3 negative |
| po4_ppm | float64 | 100.0% | 0 |  |
| so4_ppm | float64 | 100.0% | 0 |  |
| methods | str | 0.0% | 23 | top: SR1, SR2(7578), LL1-DN, LL1-NA(7113), SR1, SR2, SR3-AA;CA;FE;XU;XX(5476) |
| tapefile | str | 0.0% | 22 | top: XG0602.01(7741), XG0012.04(1883), XG0499.07(1790) |
| reformat | str | 12.9% | 172 | top: SUPPLEMENTAL ANALYSIS DATA ADDED FROM XG0602.04 RECORD: GOLD VALUE(-.01) ADDED BASED ON GJBX(82)-135 EXPLANATION:(4712), GOLD VALUE(-.01) ADDED BASED ON GJBX(82)-135 EXPLANATION:(2584), CONCENTRATIONS BELOW DETECTION LIMIT (NEGATIVE VALUES) ADDED FROM TABLE 2 IN GJBX-89(79):(1568) |
| coordprb | str | 75.1% | 1149 | top: COORDINATES CHANGED TO CORRESPONDING XG0499.07 VALUES TO RECOVER SIGNIFICANT DIGITS:(2296), COORDINATES ADDED FROM CORRESPONDING XG0602.01 RECORD TO RECOVER SIGNIFICANT DIGITS:(1577), LONGITUDE CHANGED TO CORRESPONDING XG0499.07 VALUE TO RECOVER SIGNIFICANT DIGITS:(1140) |
| comments | float64 | 100.0% | 0 |  |
| comment2 | float64 | 100.0% | 0 |  |
