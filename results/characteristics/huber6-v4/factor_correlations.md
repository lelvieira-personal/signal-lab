# Factor correlations, `huber6-v4` (decisions/0058)

Weeks with all six factors: 1093, from 1999-01-01 to 2019-12-27.

Full-sample correlation:

```
             equity  real_yield  inflation  credit  dollar  commodities
equity         1.00        0.02       0.40   -0.37   -0.28         0.41
real_yield     0.02        1.00      -0.16   -0.25    0.28        -0.09
inflation      0.40       -0.16       1.00   -0.36   -0.13         0.33
credit        -0.37       -0.25      -0.36    1.00   -0.03        -0.16
dollar        -0.28        0.28      -0.13   -0.03    1.00        -0.40
commodities    0.41       -0.09       0.33   -0.16   -0.40         1.00
```

Range of the rolling 156-week correlation, by pair:

- `equity~real_yield`: -0.28 to 0.40
- `equity~inflation`: -0.03 to 0.68
- `equity~credit`: -0.64 to -0.07
- `equity~dollar`: -0.60 to 0.11
- `equity~commodities`: 0.03 to 0.72
- `real_yield~inflation`: -0.50 to 0.33
- `real_yield~credit`: -0.59 to 0.07
- `real_yield~dollar`: 0.00 to 0.46
- `real_yield~commodities`: -0.34 to 0.18
- `inflation~credit`: -0.57 to -0.02
- `inflation~dollar`: -0.49 to 0.27
- `inflation~commodities`: 0.05 to 0.63
- `credit~dollar`: -0.28 to 0.15
- `credit~commodities`: -0.32 to 0.08
- `dollar~commodities`: -0.60 to -0.10
