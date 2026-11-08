"""Opracowanie wynikow cw. 1 (skutecznosc ekranowania przeslon i szczelin).

Dane: pliki Touchstone .s2p (format RI) z VNA Tektronix TTR506A, przekazane
przez prowadzacego: odleglosc anten 1,8 m, polaryzacja pionowa.

Skrypt:
  * wczytuje S12 (oraz S22) z kazdego pliku i przelicza na dB,
  * wyznacza zakres dynamiki D = S12_ref - S12_dyn,
  * wyznacza skutecznosc ekranowania SE = S12_ref - S12_x,
  * wygladza przebiegi srednia kroczaca (9 pkt = 200 MHz) do wykresow porownawczych,
  * zapisuje pliki .dat dla pgfplots oraz wiersze tabel LaTeX (katalog tabele/).

Uruchomienie:  python opracowanie.py
"""
import os
import numpy as np

KAT = os.path.dirname(os.path.abspath(__file__))
DANE = os.path.join(KAT, 'od_kaliszuka', 'ekranowanie_1_8m_V')
WYJ_DAT = os.path.join(KAT, 'dane')
WYJ_TAB = os.path.join(KAT, 'tabele')
C0 = 299_792_458.0

# klucz -> (plik, liczba otworow N, srednica d [cm])
PRZESLONY = {
    '100x1': ('przeslona_100x1cm.s2p', 100, 1.0),
    '16x2':  ('przeslona_16x2cm.s2p', 16, 2.0),
    '16x3':  ('przeslona_16x3cm.s2p', 16, 3.0),
    '100x3': ('przeslona_100x3cm.s2p', 100, 3.0),
    '4x6':   ('przeslona_4x6cm.s2p', 4, 6.0),
    '36x6':  ('przeslona_36x6cm.s2p', 36, 6.0),
    '16x8':  ('przeslona_16x8cm.s2p', 16, 8.0),
    '1x12':  ('przeslona_1x12cm.s2p', 1, 12.0),
    '4x12':  ('przeslona_4x12c,.s2p', 4, 12.0),   # literowka w nazwie pliku zrodlowego
}
SZCZELINY = {'sz15': ('szczelina_1_5cm.s2p', 1.5), 'sz18': ('szczelina_1_8cm.s2p', 1.8)}

# Szum wlasny TTR506A (karta katalogowa, 200 MHz - 6 GHz): <= -125 dBm/Hz (spec.), -130 dBm/Hz (typ.)
N0_SPEC, N0_TYP = -125.0, -130.0
IFBW = 10e3      # Hz, nastawa z plikow stanu .cstate zapisanych na stanowisku
P_PORT = 0.0     # dBm, moc wyjsciowa portu (j.w.)
SZUM_SPEC = N0_SPEC + 10 * np.log10(IFBW) - P_PORT   # dB wzgledem nadajnika
SZUM_TYP = N0_TYP + 10 * np.log10(IFBW) - P_PORT

F_TAB = [0.8, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 5.8]   # GHz, do tabel
N_WYGL = 9


def wczytaj(nazwa):
    a = np.loadtxt(os.path.join(DANE, nazwa), comments=['!', '#'])
    f = a[:, 0] / 1e9
    s12 = a[:, 5] + 1j * a[:, 6]
    s22 = a[:, 7] + 1j * a[:, 8]
    return f, a[:, 5], a[:, 6], 20 * np.log10(np.abs(s12)), 20 * np.log10(np.abs(s22))


def wygladz(y, n=N_WYGL):
    """Srednia kroczaca o oknie n punktow; na brzegach okno skraca sie symetrycznie."""
    h = n // 2
    return np.array([y[max(0, i - h):i + h + 1].mean() for i in range(len(y))])


def pl(x, nd=1, znak=False):
    s = f'{x:+.{nd}f}' if znak else f'{x:.{nd}f}'
    return s.replace('.', ',')


def main():
    os.makedirs(WYJ_DAT, exist_ok=True)
    os.makedirs(WYJ_TAB, exist_ok=True)

    f, re_ref, im_ref, ref, s22_ref = wczytaj('referencja.s2p')
    _, _, _, dyn, _ = wczytaj('dynamika.s2p')
    D = ref - dyn
    se = {k: ref - wczytaj(v[0])[3] for k, v in PRZESLONY.items()}
    s12p = {k: wczytaj(v[0])[3] for k, v in PRZESLONY.items()}
    ses = {k: ref - wczytaj(v[0])[3] for k, v in SZCZELINY.items()}
    s12s = {k: wczytaj(v[0])[3] for k, v in SZCZELINY.items()}
    idx = [int(np.argmin(np.abs(f - x))) for x in F_TAB]

    # ---------- pliki .dat dla pgfplots ----------
    kol = ['f', 'ref', 'dyn', 'D', 'Dg', 'Dmax', 'refg', 'dyng', 'S22']
    tab = [f, ref, dyn, D, wygladz(D), ref - SZUM_SPEC, wygladz(ref), wygladz(dyn), s22_ref]
    for k in se:
        kol += [f'SE{k}', f'SE{k}g']
        tab += [se[k], wygladz(se[k])]
    for k in ses:
        kol += [f'SE{k}', f'SE{k}g']
        tab += [ses[k], wygladz(ses[k])]
    np.savetxt(os.path.join(WYJ_DAT, 'wyniki.dat'), np.column_stack(tab),
               header=' '.join(kol), comments='', fmt='%.4f')

    # ---------- tabele ----------
    def zapisz(nazwa, wiersze):
        with open(os.path.join(WYJ_TAB, nazwa), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(wiersze) + '\n')

    # T1: S12 referencja, dynamika, szczeliny (wyniki pomiarow)
    zapisz('t_s12_ref.tex', [
        f'{pl(f[i], 2)} & {pl(re_ref[i], 5)} & {pl(im_ref[i], 5)} & {pl(ref[i])} & {pl(dyn[i])} & '
        f'{pl(s12s["sz15"][i])} & {pl(s12s["sz18"][i])} \\\\' for i in idx])
    # T2: S12 przeslon
    zapisz('t_s12_przeslony.tex', [
        f'{pl(f[i], 2)} & ' + ' & '.join(pl(s12p[k][i]) for k in PRZESLONY) + ' \\\\' for i in idx])
    # T3: zakres dynamiki
    zapisz('t_dynamika.tex', [
        f'{pl(f[i], 2)} & {pl(ref[i])} & {pl(dyn[i])} & {pl(D[i])} & {pl(ref[i] - SZUM_SPEC)} & '
        f'{pl(dyn[i] - SZUM_SPEC, znak=True)} \\\\' for i in idx])
    # T4: SE przeslon
    zapisz('t_se_przeslony.tex', [
        f'{pl(f[i], 2)} & ' + ' & '.join(pl(se[k][i]) for k in PRZESLONY) + f' & {pl(D[i])} \\\\'
        for i in idx])
    # T5: SE szczelin
    zapisz('t_se_szczeliny.tex', [
        f'{pl(f[i], 2)} & {pl(ses["sz15"][i])} & {pl(ses["sz18"][i])} & '
        f'{pl(ses["sz15"][i] - ses["sz18"][i], znak=True)} & {pl(D[i])} \\\\' for i in idx])

    # T6: zestawienie charakterystyczne przeslon (wygladzone)
    wiersze, raport = [], []
    for k, (plik, N, d) in PRZESLONY.items():
        fg = C0 / (2 * d / 100) / 1e9
        g = wygladz(se[k])
        m = f < min(fg, 5.8)
        if min(fg, 5.8) / f[0] >= 2:   # dopasowanie prostej tylko gdy zakres < f_g obejmuje >= oktawe
            a, b = np.polyfit(np.log10(f[m]), g[m], 1)
            nach = pl(a, 1)
        else:
            a, nach = np.nan, '---'
        i1, i3 = [int(np.argmin(np.abs(f - x))) for x in (1.0, 3.0)]
        th = []
        for x in (1.0, 3.0):
            lam = C0 / (x * 1e9) * 100
            th.append(20 * np.log10(lam / (2 * d)) - 10 * np.log10(N))
        frac = 100 * np.mean(se[k] > D - 6)
        fg_s = pl(fg, 2) if fg <= 5.8 else f'{pl(fg, 1)}$^{{*}}$'
        wiersze.append(f'{N}$\\times${pl(d, 0)} & {N} & {pl(d, 0)} & {fg_s} & {pl(np.mean(se[k]))} & '
                       f'{pl(g[i1])} & {pl(th[0], znak=True)} & {pl(g[i3])} & {nach} \\\\')
        raport.append((k, fg, np.mean(se[k]), g[i1], g[i3], th, a, frac))
    zapisz('t_zestawienie.tex', wiersze)

    # T7: srednie SE w pasmach (szczeliny i wybrane przeslony, na tle dynamiki)
    PASMA = [(0.8, 2.0), (2.0, 4.0), (4.0, 5.8), (0.8, 5.8)]
    def srednie(y):
        return [y[(f >= lo - 1e-9) & (f <= hi + 1e-9)].mean() for lo, hi in PASMA]
    pozycje = [('Szczelina 1,5~cm', ses['sz15']), ('Szczelina 1,8~cm', ses['sz18']),
               ('Przesłona 100$\\times$1~cm', se['100x1']), ('Przesłona 16$\\times$2~cm', se['16x2']),
               ('Przesłona 16$\\times$3~cm', se['16x3']), ('Zakres dynamiki $D$', D)]
    zapisz('t_pasma.tex', [f'{n} & ' + ' & '.join(pl(v) for v in srednie(y)) + ' \\\\' for n, y in pozycje])
    for n, y in pozycje:
        print('PASMA', n, [round(v, 1) for v in srednie(y)])

    # ---------- raport kontrolny ----------
    print(f'Zakres f: {f[0]:.3f}-{f[-1]:.3f} GHz, krok {1000*(f[1]-f[0]):.0f} MHz, N={len(f)}')
    print(f'Szum (IFBW {IFBW/1e3:.0f} kHz, {P_PORT} dBm): spec {SZUM_SPEC:.1f} dB, typ {SZUM_TYP:.1f} dB')
    print(f'D: min {D.min():.1f} @ {f[D.argmin()]:.3f}, max {D.max():.1f} @ {f[D.argmax()]:.3f}, '
          f'srednia {D.mean():.1f}, mediana {np.median(D):.1f}')
    print(f'dyn: srednia {dyn.mean():.1f}, mediana {np.median(dyn):.1f}, max {dyn.max():.1f} @ {f[dyn.argmax()]:.3f}, '
          f'pkt powyzej szumu spec: {np.mean(dyn > SZUM_SPEC)*100:.0f}%')
    print(f'ref: min {ref.min():.1f} @ {f[ref.argmin()]:.3f}, max {ref.max():.1f} @ {f[ref.argmax()]:.3f}')
    print(f'S22 > -10 dB: {np.mean(s22_ref > -10)*100:.0f}% punktow')
    for k, fg, sm, g1, g3, th, a, frac in raport:
        print(f'{k:6s} fg={fg:6.2f} sr={sm:5.1f} g1={g1:5.1f} th1={th[0]:6.1f} g3={g3:5.1f} th3={th[1]:6.1f} '
              f'nachyl={a:6.1f} pkt_przy_D={frac:3.0f}% neg={np.mean(se[k] < 0)*100:3.0f}%')
    for k in ses:
        g = wygladz(ses[k])
        print(f'{k}: sr={ses[k].mean():.1f} min={ses[k].min():.1f} max={ses[k].max():.1f} '
              f'g@1={g[np.argmin(abs(f-1))]:.1f} g@3={g[np.argmin(abs(f-3))]:.1f} g@5={g[np.argmin(abs(f-5))]:.1f}')
    r = ses['sz15'] - ses['sz18']
    print(f'roznica sz15-sz18: srednia {r.mean():.1f}, mediana {np.median(r):.1f}, '
          f'wygl. max {wygladz(r).max():.1f} @ {f[wygladz(r).argmax()]:.3f}, % >0: {np.mean(r>0)*100:.0f}')
    print(f'sz15 - 16x2 srednio {np.mean(ses["sz15"]-se["16x2"]):.1f}; sz15 - 100x1 {np.mean(ses["sz15"]-se["100x1"]):.1f}')


if __name__ == '__main__':
    main()
