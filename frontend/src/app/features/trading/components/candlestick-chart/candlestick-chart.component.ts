import {
  Component,
  Input,
  OnChanges,
  SimpleChanges,
  AfterViewInit,
  OnDestroy,
  ElementRef,
  ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription, interval } from 'rxjs';
import { createChart, CandlestickData, LineData, Time } from 'lightweight-charts';
import { TradingService, OhlcvData } from '../../../../core/services/trading.service';

@Component({
  selector: 'app-candlestick-chart',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './candlestick-chart.component.html',
  styleUrls: ['./candlestick-chart.component.scss']
})
export class CandlestickChartComponent implements AfterViewInit, OnChanges, OnDestroy {
  @Input() symbol: string = 'BTC-USD';
  @ViewChild('chartContainer') chartContainer!: ElementRef;
  @ViewChild('indicatorContainer') indicatorContainer!: ElementRef;

  // Use 'any' for runtime compatibility across minor library versions
  private chart: any;
  private candlestickSeries: any;
  private indicatorChart: any;
  private indicatorSeries: any;
  private overlaySeries: any[] = [];

  private refreshSub?: Subscription;
  private lastOhlcvData: OhlcvData[] = [];

  timeframes = ['1m', '5m', '15m', '30m', '1h', '6h', '12h', '1d'];
  activeTimeframe = '1h';

  indicators = [
    { id: 'none', label: 'None' },
    { id: 'rsi14', label: 'RSI (14)' },
    { id: 'macd', label: 'MACD (12,26,9)' },
    { id: 'sma50', label: 'SMA (50)' },
    { id: 'ema20', label: 'EMA (20)' },
    { id: 'bbands', label: 'Bollinger Bands (20, 2)' },
  ];
  activeIndicator: 'none' | 'rsi14' | 'macd' | 'sma50' | 'ema20' | 'bbands' = 'none';

  constructor(private tradingService: TradingService) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['symbol'] && this.chart) {
      this.loadChartData();
    }
  }

  ngAfterViewInit(): void {
    this.createChart();
    this.loadChartData();
    // Auto-refresh chart data every 30 seconds
    this.refreshSub = interval(30_000).subscribe(() => this.loadChartData());
    window.addEventListener('resize', this.resizeChart);
  }
  
  createChart(): void {
    const chartOptions = {
      layout: {
        background: { color: '#0b0e11' },
        textColor: '#eaecef',
      },
      grid: {
        vertLines: { color: '#1e2329' },
        horzLines: { color: '#1e2329' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: '#2B3139',
      },
      rightPriceScale: {
        borderColor: '#2B3139',
      },
    };
    this.chart = (createChart as any)(
      this.chartContainer.nativeElement,
      chartOptions
    );
    const seriesOptions = {
      upColor: '#02c076',
      downColor: '#f6465d',
      borderDownColor: '#f6465d',
      borderUpColor: '#02c076',
      wickDownColor: '#f6465d',
      wickUpColor: '#02c076',
    };
    this.candlestickSeries = this.chart.addCandlestickSeries(seriesOptions);

    // Prepare indicator chart (separate pane below main chart)
    if (this.indicatorContainer) {
      this.indicatorChart = (createChart as any)(this.indicatorContainer.nativeElement, {
        layout: {
          background: { color: '#0b0e11' },
          textColor: '#eaecef',
        },
        rightPriceScale: {
          borderColor: '#2B3139',
        },
        timeScale: {
          visible: false, // share time visually with main chart
        },
        grid: {
          vertLines: { color: '#1e2329' },
          horzLines: { color: '#1e2329' },
        },
      });

      this.indicatorSeries = this.indicatorChart.addLineSeries({
        color: '#F0B90B',
        lineWidth: 1,
      });
    }
  }

  loadChartData(): void {
    if (!this.candlestickSeries || !this.symbol) {
      return;
    }

    this.tradingService
      .getOhlcvData(this.symbol, this.activeTimeframe)
      .subscribe({
        next: (response) => {
          if (!response || !response.data || response.data.length === 0) {
            console.warn(
              'No OHLCV data returned for',
              this.symbol,
              this.activeTimeframe,
              response
            );
            this.candlestickSeries.setData([]);
            this.updateIndicator([]);
            return;
          }

          this.lastOhlcvData = response.data;

          const data: CandlestickData[] = response.data.map((d) => ({
            // Backend sends Unix seconds; lightweight-charts expects Time/UTCTimestamp-compatible value
            time: d.time as Time,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }));

      this.candlestickSeries.setData(data);
      this.chart.timeScale().fitContent();

          this.updateIndicator(this.lastOhlcvData);
        },
        error: (err) => {
          console.error(
            'Failed to load OHLCV data for',
            this.symbol,
            this.activeTimeframe,
            err
          );
          this.candlestickSeries.setData([]);
          this.updateIndicator([]);
        },
    });
  }
  
  setTimeframe(timeframe: string): void {
    this.activeTimeframe = timeframe;
    this.loadChartData();
  }

  setIndicator(indicatorId: 'none' | 'rsi14' | 'macd' | 'sma50' | 'ema20' | 'bbands'): void {
    this.activeIndicator = indicatorId;
    this.updateIndicator(this.lastOhlcvData);
  }

  private updateIndicator(ohlcv: OhlcvData[]): void {
    // Clear any existing overlay series on the main chart
    if (this.chart && this.overlaySeries.length) {
      this.overlaySeries.forEach((s) => {
        try {
          this.chart.removeSeries(s);
        } catch {
          // ignore
        }
      });
      this.overlaySeries = [];
    }

    // Clear indicator pane series
    if (this.indicatorSeries) {
      this.indicatorSeries.setData([]);
    }

    if (!ohlcv || ohlcv.length === 0) {
      return;
    }

    switch (this.activeIndicator) {
      case 'none':
        return;

      case 'rsi14': {
        const rsiData = this.calculateRsi(ohlcv, 14);
        if (this.indicatorSeries) {
          this.indicatorSeries.setData(rsiData);
        }
        return;
      }

      case 'macd': {
        const macdData = this.calculateMacd(ohlcv, 12, 26, 9);
        if (this.indicatorSeries) {
          this.indicatorSeries.setData(macdData);
        }
        return;
      }

      case 'sma50': {
        if (!this.chart) return;
        const sma = this.calculateSma(ohlcv, 50);
        const series = this.chart.addLineSeries({
          color: '#F0B90B',
          lineWidth: 1,
        });
        series.setData(sma);
        this.overlaySeries.push(series);
        return;
      }

      case 'ema20': {
        if (!this.chart) return;
        const ema = this.calculateEma(ohlcv, 20);
        const series = this.chart.addLineSeries({
          color: '#03a9f4',
          lineWidth: 1,
        });
        series.setData(ema);
        this.overlaySeries.push(series);
        return;
      }

      case 'bbands': {
        if (!this.chart) return;
        const { basis, upper, lower } = this.calculateBollingerBands(ohlcv, 20, 2);
        const basisSeries = this.chart.addLineSeries({
          color: '#F0B90B',
          lineWidth: 1,
        });
        const upperSeries = this.chart.addLineSeries({
          color: '#848E9C',
          lineWidth: 1,
        });
        const lowerSeries = this.chart.addLineSeries({
          color: '#848E9C',
          lineWidth: 1,
        });
        basisSeries.setData(basis);
        upperSeries.setData(upper);
        lowerSeries.setData(lower);
        this.overlaySeries.push(basisSeries, upperSeries, lowerSeries);
        return;
      }
    }
  }

  private calculateRsi(ohlcv: OhlcvData[], period: number): LineData[] {
    if (ohlcv.length <= period) return [];

    const closes = ohlcv.map((c) => c.close);
    const times = ohlcv.map((c) => c.time as Time);

    const gains: number[] = [];
    const losses: number[] = [];

    for (let i = 1; i < closes.length; i++) {
      const diff = closes[i] - closes[i - 1];
      gains.push(Math.max(diff, 0));
      losses.push(Math.max(-diff, 0));
    }

    // First average gain/loss
    let avgGain = 0;
    let avgLoss = 0;
    for (let i = 0; i < period; i++) {
      avgGain += gains[i];
      avgLoss += losses[i];
    }
    avgGain /= period;
    avgLoss /= period;

    const rsiPoints: LineData[] = [];

    // First RSI value corresponds to index period
    let rs = avgLoss === 0 ? 0 : avgGain / avgLoss;
    let rsi = avgLoss === 0 ? 100 : 100 - 100 / (1 + rs);
    rsiPoints.push({ time: times[period] as Time, value: rsi });

    // Wilder's smoothing
    for (let i = period + 1; i < closes.length; i++) {
      const gain = gains[i - 1];
      const loss = losses[i - 1];
      avgGain = (avgGain * (period - 1) + gain) / period;
      avgLoss = (avgLoss * (period - 1) + loss) / period;

      rs = avgLoss === 0 ? 0 : avgGain / avgLoss;
      rsi = avgLoss === 0 ? 100 : 100 - 100 / (1 + rs);

      rsiPoints.push({ time: times[i] as Time, value: rsi });
    }

    return rsiPoints;
  }

  private calculateSma(ohlcv: OhlcvData[], period: number): LineData[] {
    if (ohlcv.length < period) return [];
    const closes = ohlcv.map((c) => c.close);
    const times = ohlcv.map((c) => c.time as Time);
    const result: LineData[] = [];

    let sum = 0;
    for (let i = 0; i < closes.length; i++) {
      sum += closes[i];
      if (i >= period) {
        sum -= closes[i - period];
      }
      if (i >= period - 1) {
        const value = sum / period;
        result.push({ time: times[i], value });
      }
    }
    return result;
  }

  private calculateEma(ohlcv: OhlcvData[], period: number): LineData[] {
    if (ohlcv.length < period) return [];
    const closes = ohlcv.map((c) => c.close);
    const times = ohlcv.map((c) => c.time as Time);
    const result: LineData[] = [];

    const k = 2 / (period + 1);

    // Start EMA at SMA of first period
    let ema = 0;
    let sum = 0;
    for (let i = 0; i < period; i++) {
      sum += closes[i];
    }
    ema = sum / period;
    result.push({ time: times[period - 1], value: ema });

    for (let i = period; i < closes.length; i++) {
      ema = closes[i] * k + ema * (1 - k);
      result.push({ time: times[i], value: ema });
    }

    return result;
  }

  private calculateMacd(
    ohlcv: OhlcvData[],
    fastPeriod: number,
    slowPeriod: number,
    signalPeriod: number
  ): LineData[] {
    if (ohlcv.length < slowPeriod + signalPeriod) return [];

    const closes = ohlcv.map((c) => c.close);
    const times = ohlcv.map((c) => c.time as Time);

    const fastEma = this.calculateEmaSeries(closes, fastPeriod);
    const slowEma = this.calculateEmaSeries(closes, slowPeriod);

    const macdLine: number[] = [];
    const macdTimes: Time[] = [];

    for (let i = 0; i < closes.length; i++) {
      if (fastEma[i] != null && slowEma[i] != null) {
        macdLine[i] = fastEma[i]! - slowEma[i]!;
        macdTimes[i] = times[i];
      } else {
        macdLine[i] = NaN;
      }
    }

    // Signal line EMA of MACD line
    const signal = this.calculateEmaSeries(
      macdLine.map((v) => (Number.isFinite(v) ? v : 0)),
      signalPeriod,
      macdLine.map((v) => Number.isFinite(v))
    );

    // For simplicity display MACD line only in this first version
    const result: LineData[] = [];
    for (let i = 0; i < macdLine.length; i++) {
      if (Number.isFinite(macdLine[i]) && signal[i] != null) {
        result.push({ time: macdTimes[i], value: macdLine[i] });
      }
    }

    return result;
  }

  // Helper: EMA over arbitrary numeric array, with optional mask for valid values
  private calculateEmaSeries(
    values: number[],
    period: number,
    validMask?: boolean[]
  ): Array<number | null> {
    const result: Array<number | null> = new Array(values.length).fill(null);
    if (values.length < period) return result;

    const k = 2 / (period + 1);

    // Initial SMA over first 'period' valid points
    let sum = 0;
    let count = 0;
    let idx = 0;
    while (idx < values.length && count < period) {
      if (!validMask || validMask[idx]) {
        sum += values[idx];
        count++;
      }
      idx++;
    }
    if (count < period) return result;

    let ema = sum / count;
    result[idx - 1] = ema;

    for (let i = idx; i < values.length; i++) {
      if (validMask && !validMask[i]) continue;
      ema = values[i] * k + ema * (1 - k);
      result[i] = ema;
    }
    return result;
  }

  private calculateBollingerBands(
    ohlcv: OhlcvData[],
    period: number,
    stdDevMult: number
  ): { basis: LineData[]; upper: LineData[]; lower: LineData[] } {
    const closes = ohlcv.map((c) => c.close);
    const times = ohlcv.map((c) => c.time as Time);

    const basis: LineData[] = [];
    const upper: LineData[] = [];
    const lower: LineData[] = [];

    if (closes.length < period) return { basis, upper, lower };

    for (let i = period - 1; i < closes.length; i++) {
      const slice = closes.slice(i - period + 1, i + 1);
      const mean = slice.reduce((a, b) => a + b, 0) / period;
      const variance =
        slice.reduce((acc, v) => acc + (v - mean) * (v - mean), 0) / period;
      const std = Math.sqrt(variance);

      const t = times[i];
      basis.push({ time: t, value: mean });
      upper.push({ time: t, value: mean + stdDevMult * std });
      lower.push({ time: t, value: mean - stdDevMult * std });
    }

    return { basis, upper, lower };
  }

  resizeChart = () => {
    if (this.chart && this.chartContainer.nativeElement.clientWidth) {
      this.chart.resize(
        this.chartContainer.nativeElement.clientWidth,
        this.chartContainer.nativeElement.clientHeight
      );
    }
    if (this.indicatorChart && this.indicatorContainer?.nativeElement.clientWidth) {
      this.indicatorChart.resize(
        this.indicatorContainer.nativeElement.clientWidth,
        this.indicatorContainer.nativeElement.clientHeight
      );
    }
  }

  ngOnDestroy(): void {
    if (this.refreshSub) {
      this.refreshSub.unsubscribe();
    }
    if (this.chart) {
      this.chart.remove();
    }
    if (this.indicatorChart) {
      this.indicatorChart.remove();
    }
    window.removeEventListener('resize', this.resizeChart);
  }
}
