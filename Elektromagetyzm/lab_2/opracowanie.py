"""Opracowanie wynikow cw. 2 (zaburzenia przewodzone, siec sztuczna, odbiornik R&S ESL3).

Skrypt:
  * wczytuje listy pikow pomiaru koncowego (*.DAT, eksport "Peak List Export"),
  * liczy poziom dopuszczalny PN-EN 55032 (klasa B) dla detektora QP i AV,
  * sprawdza, czy obliczony margines zgadza sie z "Delta Limit" z odbiornika,
  * zapisuje wiersze tabel LaTeX (tabele/) i pliki .dat dla pgfplots (dane/).

Uruchomienie:  python3 opracowanie.py
"""
import math
import os

KAT = os.path.dirname(os.path.abspath(__file__))

# plik wejsciowy -> nazwa wyjsciowa
POMIARY = {
    'lampka-niepodlaczona.DAT': 'bez_L1',
    'lampka-podlaczona.DAT': 'lampka_L1',
    'linia2-lapka-wlaczona.DAT': 'lampka_N',
    'linia-2-bez-lampka.DAT': 'bez_N',
}


def limit(f_mhz, det):
    """Poziom dopuszczalny PN-EN 55032 kl. B [dBuV]; w 0,15-0,5 MHz liniowo wzgledem log f."""
    if f_mhz < 0.5:
        qp = 66 - 10 * math.log10(f_mhz / 0.15) / math.log10(0.5 / 0.15)
    elif f_mhz < 5:
        qp = 56.0
    else:
        qp = 60.0
    return qp if det == 'QP' else qp - 10


def wczytaj(nazwa):
    """Zwraca liste (f_MHz, detektor, poziom_dBuV, delta_z_odbiornika)."""
    with open(os.path.join(KAT, 'wyniki', nazwa), encoding='latin-1') as fh:
        linie = fh.read().splitlines()
    i = next(k for k, l in enumerate(linie) if l.startswith('Values;'))
    wyn = []
    for l in linie[i + 1:]:
        p = l.split(';')
        if len(p) < 4 or not p[1]:
            continue
        wyn.append((float(p[1]) / 1e6, 'QP' if p[0] == '1' else 'AV', float(p[2]), float(p[3])))
    return sorted(wyn)


def pl(x, nd=2, znak=False):
    s = f'{x:+.{nd}f}' if znak else f'{x:.{nd}f}'
    return s.replace('.', '{,}')


def main():
    for nazwa, wy in POMIARY.items():
        dane = wczytaj(nazwa)
        wiersze, pliki = [], {'QP': ['f U'], 'AV': ['f U']}
        for f, det, u, d_odb in dane:
            lim = limit(f, det)
            d = u - lim
            assert abs(d - d_odb) < 0.01, (nazwa, f, det, d, d_odb)   # zgodnosc z odbiornikiem
            ocena = 'nie spełnia' if d > 0 else 'spełnia'
            wiersze.append(f'{f * 1000:.0f} & {det} & {pl(u)} & {pl(lim)} & {pl(d, znak=True)} & {ocena} \\\\')
            pliki[det].append(f'{f:.4f} {u:.2f}')
        with open(os.path.join(KAT, 'tabele', f't_{wy}.tex'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(wiersze) + '\n')
        for det, w in pliki.items():
            with open(os.path.join(KAT, 'dane', f'{wy}_{det.lower()}.dat'), 'w') as fh:
                fh.write('\n'.join(w) + '\n')
        qp = [d for d in dane if d[1] == 'QP']
        av = [d for d in dane if d[1] == 'AV']
        mx = lambda s: max(s, key=lambda r: r[2] - limit(r[0], r[1])) if s else None
        print(f'{wy:10s} n={len(dane):2d}  max QP-L: {mx(qp)}  max AV-L: {mx(av)}')

    # kontrola wzoru granicznego na krancach przedzialu
    assert abs(limit(0.15, 'QP') - 66) < 1e-9 and abs(limit(0.4999999, 'QP') - 56) < 1e-4
    assert limit(4.998, 'QP') == 56 and limit(5.0, 'AV') == 50


if __name__ == '__main__':
    main()
