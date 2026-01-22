import { Component, OnInit, ViewChild, ElementRef, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Observable, Subscription } from 'rxjs';
import { createChart, CandlestickData, Time, LineData } from 'lightweight-charts';

import { PairSwitcherComponent } from '../trading/components/pair-switcher/pair-switcher.component';
import { MarketDataService, MarketDataResponse } from '../../core/services/market-data.service';
import { 
  SimulatorService, 
  SimulatorCalculation, 
  LeaderboardEntry,
  OHLCVData 
} from '../../core/services/simulator.service';

type SimulationStep = 'config' | 'analysis' | 'results';

@Component({
  selector: 'app-simulator-page',
  standalone: true,
  imports: [CommonModule, FormsModule, PairSwitcherComponent],
  templateUrl: './simulator-page.component.html',
  styleUrls: ['./simulator-page.component.scss']
})
export class SimulatorPageComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('chartContainer') chartContainer!: ElementRef;

  // Market data for pair selection
  public marketData$: Observable<MarketDataResponse | null>;

  // Step management
  currentStep: SimulationStep = 'config';

  // Configuration
  selectedPair: string = 'BTC-USD';
  startDate: string = '';
  endDate: string = '';
  
  // Form values
  entryPrice: number = 0;
  stopLoss: number = 0;
  takeProfit: number = 0;

  // Chart
  private chart: any;
  private candlestickSeries: any;
  private entryLine: any;
  private slLine: any;
  private tpLine: any;
  private hiddenData: OHLCVData[] = [];
  private visibleData: OHLCVData[] = [];
  private allData: OHLCVData[] = [];

  // Timeframe
  timeframes = ['15m', '30m', '1h', '4h', '1d'];
  activeTimeframe = '1h';

  // Results
  simulationResult: SimulatorCalculation | null = null;
  isLoading = false;
  errorMessage = '';

  // Leaderboard
  leaderboard: LeaderboardEntry[] = [];
  leaderboardLoading = false;

  private subscriptions: Subscription[] = [];

  constructor(
    private marketDataService: MarketDataService,
    private simulatorService: SimulatorService
  ) {
    this.marketData$ = this.marketDataService.prices$;
    this.initializeDates();
  }

  ngOnInit(): void {
    this.loadLeaderboard();
  }

  ngAfterViewInit(): void {
    this.createChart();
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach(sub => sub.unsubscribe());
    if (this.chart) {
      this.chart.remove();
    }
    window.removeEventListener('resize', this.resizeChart);
  }

  private initializeDates(): void {
    // Default: 30 days ago to today
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    // Format for input[type="date"]
    this.endDate = this.formatDateForInput(today);
    this.startDate = this.formatDateForInput(thirtyDaysAgo);
  }

  private formatDateForInput(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  selectPair(pair: string): void {
    this.selectedPair = pair;
    if (this.currentStep === 'analysis') {
      this.loadChartData();
    }
  }

  onDateChange(): void {
    // Reset when dates change
    if (this.currentStep !== 'config') {
      this.currentStep = 'config';
      this.simulationResult = null;
    }
  }

  startSimulation(): void {
    if (!this.validateDates()) {
      return;
    }

    this.currentStep = 'analysis';
    this.loadChartData();
    this.loadEntryPrice();
  }

  private validateDates(): boolean {
    const start = new Date(this.startDate + 'T00:00:00Z');
    const end = new Date(this.endDate + 'T23:59:59Z');
    
    if (start >= end) {
      this.errorMessage = 'Start date must be before end date';
      return false;
    }

    const today = new Date();
    if (end > today) {
      this.errorMessage = 'End date cannot be in the future';
      return false;
    }

    this.errorMessage = '';
    return true;
  }

  private createChart(): void {
    if (!this.chartContainer) return;

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
      crosshair: {
        mode: 1,
      },
    };

    this.chart = (createChart as any)(this.chartContainer.nativeElement, chartOptions);
    
    const seriesOptions = {
      upColor: '#02c076',
      downColor: '#f6465d',
      borderDownColor: '#f6465d',
      borderUpColor: '#02c076',
      wickDownColor: '#f6465d',
      wickUpColor: '#02c076',
    };
    
    this.candlestickSeries = this.chart.addCandlestickSeries(seriesOptions);
    
    window.addEventListener('resize', this.resizeChart);
  }

  private loadChartData(): void {
    if (!this.chart || !this.selectedPair) return;

    this.isLoading = true;
    
    // Parse dates as UTC to avoid timezone issues
    const startDate = new Date(this.startDate + 'T00:00:00Z');
    const endDate = new Date(this.endDate + 'T23:59:59Z');

    // Load data from a period BEFORE start date for analysis context
    // User sees historical data leading up to start date (30 days before)
    const historicalStart = new Date(startDate);
    historicalStart.setDate(historicalStart.getDate() - 30); // 30 days of visible history

    const sub = this.simulatorService.getHistoricalData(
      this.selectedPair,
      historicalStart,
      endDate,
      this.activeTimeframe
    ).subscribe({
      next: (response) => {
        if (!response || !response.data || response.data.length === 0) {
          this.errorMessage = 'No data available for this period';
          this.isLoading = false;
          return;
        }

        this.allData = response.data;
        
        // Use UTC timestamp for comparison (Binance returns UTC timestamps)
        const startTimestamp = Math.floor(startDate.getTime() / 1000);

        // Split data: visible (before or at start date) and hidden (after start date)
        this.visibleData = response.data.filter(d => d.time <= startTimestamp);
        this.hiddenData = response.data.filter(d => d.time > startTimestamp);

        // If no visible data, show a message
        if (this.visibleData.length === 0) {
          this.errorMessage = 'No historical data available before the start date. Try selecting an earlier date.';
          this.isLoading = false;
          return;
        }

        // Show only the visible data
        this.setChartData(this.visibleData);
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error loading chart data:', err);
        this.errorMessage = 'Failed to load chart data';
        this.isLoading = false;
      }
    });

    this.subscriptions.push(sub);
  }

  private loadEntryPrice(): void {
    // Parse as UTC to match chart data
    const startDate = new Date(this.startDate + 'T00:00:00Z');
    
    const sub = this.simulatorService.getPriceAtDate(this.selectedPair, startDate).subscribe({
      next: (response) => {
        this.entryPrice = Math.round(response.price * 100) / 100;
        // Set default SL and TP (5% below and above entry)
        this.stopLoss = Math.round(this.entryPrice * 0.95 * 100) / 100;
        this.takeProfit = Math.round(this.entryPrice * 1.05 * 100) / 100;
        this.updatePriceLines();
      },
      error: (err) => {
        console.error('Error loading entry price:', err);
        // Fallback: use last visible candle close price
        if (this.visibleData.length > 0) {
          const lastCandle = this.visibleData[this.visibleData.length - 1];
          this.entryPrice = Math.round(lastCandle.close * 100) / 100;
          this.stopLoss = Math.round(this.entryPrice * 0.95 * 100) / 100;
          this.takeProfit = Math.round(this.entryPrice * 1.05 * 100) / 100;
          this.updatePriceLines();
        }
      }
    });

    this.subscriptions.push(sub);
  }

  private setChartData(data: OHLCVData[]): void {
    if (!this.candlestickSeries) return;

    const chartData: CandlestickData[] = data.map(d => ({
      time: d.time as Time,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));

    this.candlestickSeries.setData(chartData);
    this.chart.timeScale().fitContent();
  }

  updatePriceLines(): void {
    // Remove existing lines
    this.removePriceLines();

    if (!this.chart || this.entryPrice <= 0) return;

    // Add entry price line
    this.entryLine = this.chart.addLineSeries({
      color: '#F0B90B',
      lineWidth: 2,
      lineStyle: 2, // Dashed
      priceLineVisible: false,
      lastValueVisible: true,
      title: 'Entry',
    });

    // Add stop loss line
    this.slLine = this.chart.addLineSeries({
      color: '#f6465d',
      lineWidth: 2,
      lineStyle: 2,
      priceLineVisible: false,
      lastValueVisible: true,
      title: 'SL',
    });

    // Add take profit line
    this.tpLine = this.chart.addLineSeries({
      color: '#02c076',
      lineWidth: 2,
      lineStyle: 2,
      priceLineVisible: false,
      lastValueVisible: true,
      title: 'TP',
    });

    // Set data for lines (horizontal lines across the visible range)
    if (this.visibleData.length > 0) {
      const firstTime = this.visibleData[0].time;
      const lastTime = this.allData[this.allData.length - 1].time;

      this.entryLine.setData([
        { time: firstTime as Time, value: this.entryPrice },
        { time: lastTime as Time, value: this.entryPrice }
      ]);

      this.slLine.setData([
        { time: firstTime as Time, value: this.stopLoss },
        { time: lastTime as Time, value: this.stopLoss }
      ]);

      this.tpLine.setData([
        { time: firstTime as Time, value: this.takeProfit },
        { time: lastTime as Time, value: this.takeProfit }
      ]);
    }
  }

  private removePriceLines(): void {
    if (this.entryLine) {
      try { this.chart.removeSeries(this.entryLine); } catch {}
      this.entryLine = null;
    }
    if (this.slLine) {
      try { this.chart.removeSeries(this.slLine); } catch {}
      this.slLine = null;
    }
    if (this.tpLine) {
      try { this.chart.removeSeries(this.tpLine); } catch {}
      this.tpLine = null;
    }
  }

  showResults(): void {
    if (!this.validatePosition()) {
      return;
    }

    this.isLoading = true;
    const request = {
      pair: this.selectedPair,
      start_date: new Date(this.startDate + 'T00:00:00Z').toISOString(),
      end_date: new Date(this.endDate + 'T23:59:59Z').toISOString(),
      entry_price: this.entryPrice,
      stop_loss: this.stopLoss,
      take_profit: this.takeProfit
    };

    const sub = this.simulatorService.calculateResult(request).subscribe({
      next: (result) => {
        this.simulationResult = result;
        this.currentStep = 'results';
        this.revealHiddenData();
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error calculating result:', err);
        this.errorMessage = 'Failed to calculate simulation result';
        this.isLoading = false;
      }
    });

    this.subscriptions.push(sub);
  }

  private validatePosition(): boolean {
    if (this.entryPrice <= 0) {
      this.errorMessage = 'Entry price must be greater than 0';
      return false;
    }

    if (this.stopLoss <= 0) {
      this.errorMessage = 'Stop loss must be greater than 0';
      return false;
    }

    if (this.takeProfit <= 0) {
      this.errorMessage = 'Take profit must be greater than 0';
      return false;
    }

    // For long position
    if (this.takeProfit > this.entryPrice) {
      if (this.stopLoss >= this.entryPrice) {
        this.errorMessage = 'Stop loss must be below entry price for a long position';
        return false;
      }
    }
    // For short position
    else {
      if (this.stopLoss <= this.entryPrice) {
        this.errorMessage = 'Stop loss must be above entry price for a short position';
        return false;
      }
    }

    this.errorMessage = '';
    return true;
  }

  private revealHiddenData(): void {
    // Show all data including the hidden portion
    this.setChartData(this.allData);
    this.updatePriceLines();
  }

  saveResult(): void {
    if (!this.simulationResult) return;

    this.isLoading = true;
    const request = {
      pair: this.selectedPair,
      start_date: new Date(this.startDate + 'T00:00:00Z').toISOString(),
      end_date: new Date(this.endDate + 'T23:59:59Z').toISOString(),
      entry_price: this.entryPrice,
      stop_loss: this.stopLoss,
      take_profit: this.takeProfit
    };

    const sub = this.simulatorService.saveResult(request).subscribe({
      next: () => {
        this.loadLeaderboard();
        this.isLoading = false;
        alert('Result saved to leaderboard!');
      },
      error: (err) => {
        console.error('Error saving result:', err);
        this.errorMessage = 'Failed to save result. Please log in.';
        this.isLoading = false;
      }
    });

    this.subscriptions.push(sub);
  }

  resetSimulation(): void {
    this.currentStep = 'config';
    this.simulationResult = null;
    this.errorMessage = '';
    this.entryPrice = 0;
    this.stopLoss = 0;
    this.takeProfit = 0;
    this.visibleData = [];
    this.hiddenData = [];
    this.allData = [];
    this.removePriceLines();
    
    if (this.candlestickSeries) {
      this.candlestickSeries.setData([]);
    }
  }

  private loadLeaderboard(): void {
    this.leaderboardLoading = true;
    
    const sub = this.simulatorService.getLeaderboard(20).subscribe({
      next: (response) => {
        this.leaderboard = response.entries;
        this.leaderboardLoading = false;
      },
      error: (err) => {
        console.error('Error loading leaderboard:', err);
        this.leaderboardLoading = false;
      }
    });

    this.subscriptions.push(sub);
  }

  setTimeframe(tf: string): void {
    this.activeTimeframe = tf;
    if (this.currentStep === 'analysis' || this.currentStep === 'results') {
      this.loadChartData();
    }
  }

  resizeChart = (): void => {
    if (this.chart && this.chartContainer?.nativeElement?.clientWidth) {
      this.chart.resize(
        this.chartContainer.nativeElement.clientWidth,
        this.chartContainer.nativeElement.clientHeight
      );
    }
  }

  formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString();
  }

  getPnlClass(pnl: number): string {
    return pnl >= 0 ? 'positive' : 'negative';
  }
}

