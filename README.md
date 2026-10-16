# Byakugan

**The 7-9 AM range and the first presented FVG for NQ and ES**

TradingView indicator, Pine Script v6. Open source under the Mozilla Public License 2.0.

![Byakugan](images/Byakugan_to_present_mock.png)

*Mock-up of how it looks on the chart.*

**Byakugan** reads the 07:00–09:00 ET premarket range and the first presented fair value gap of the session.

## What it draws

**The 7–9 AM range** (07:00–09:00 ET):
- its high, low and midpoint (0.5);
- an optional shaded box;
- levels that run from the range open to the cut-off (11:00 ET by default).

**Extensions** in multiples of the range:
- 1.5, 2.0 and 2.5 in the direction of travel;
- −0.25, −0.5, −1.25 and −1.5 beyond the origin;
- your own custom levels.

**The 09:30 bias:** the open against the midpoint.

**The Asia / London target:** the Asia (20:00–00:00) or London (02:00–05:00) high or low in the bias direction, with its distance zone tagged on the label.

**The first presented FVG:** the first fair value gap of the session (09:30–16:00 by default) that completes within 30 minutes of the open. It is drawn with its CE (50%) and its reflection, the first opposite-direction FVG after it. The FVG can run to:
- the Byakugan cut-off (11:00);
- the session end (16:00);
- the trading day's last candle (16:59);
- the present.

## Settings

**View** sits at the top:
- theme;
- text size and colour;
- label date format and side;
- days to keep;
- how older days fade.

## How to use

- Built for **NQ / MNQ** and **ES / MES**, on intraday charts of 15 minutes or less.
- Theme: Auto follows the chart background. Any colour you pick overrides it.

## Credits

- First presented FVG concept: ICT (Michael J. Huddleston).
- Inspired by "ICT 1st Presented FVG" by tristanlee85; detection written from scratch here.

## Add it to TradingView

1. In TradingView, open the **Pine Editor** (bottom panel).
2. Copy the contents of `Byakugan_FPFVG.pine` into a new script.
3. **Save**, then **Add to chart**.

## License

Mozilla Public License 2.0, see [LICENSE](LICENSE). © Unclehk2000.

*Historical frequencies, not guarantees. Nothing here is financial advice.*
