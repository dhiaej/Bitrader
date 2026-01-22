import { Component, Input, OnChanges, SimpleChanges, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { TradingService, IndicatorInsightResponse } from '../../../../core/services/trading.service';

@Component({
  selector: 'app-indicator-assistant',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './indicator-assistant.component.html',
  styleUrls: ['./indicator-assistant.component.scss'],
})
export class IndicatorAssistantComponent implements OnInit, OnChanges {
  @Input() symbol!: string;
  @Input() timeframe: string = '1h';
  @Input() currentPrice: number | null = null;

  loading = false;
  error: string | null = null;
  insight: IndicatorInsightResponse | null = null;
  showDetails = true; // Expanded by default
  lastUpdateTime: Date | null = null;

  constructor(
    private tradingService: TradingService,
    private sanitizer: DomSanitizer
  ) {}

  ngOnInit(): void {
    // Auto-refresh removed per user request
    // Fetch insights if symbol is already set
    if (this.symbol) {
      this.fetchInsights();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['symbol'] && this.symbol) {
      this.fetchInsights();
    }
  }


  fetchInsights(): void {
    if (!this.symbol) {
      console.warn('IndicatorAssistant: No symbol provided');
      return;
    }

    this.loading = true;
    this.error = null;

    console.log('IndicatorAssistant: Fetching insights for', this.symbol, this.timeframe);

    this.tradingService.getIndicatorInsights(this.symbol, this.timeframe).subscribe({
      next: (res) => {
        console.log('IndicatorAssistant: Received response', res);
        this.insight = res;
        console.log('📰 News items received:', res.news?.length || 0, res.news);
        this.loading = false;
        this.lastUpdateTime = new Date();
      },
      error: (err) => {
        console.error('IndicatorAssistant: Failed to load indicator insights', err);
        console.error('Error details:', {
          status: err?.status,
          statusText: err?.statusText,
          message: err?.message,
          error: err?.error
        });
        this.error = err?.error?.detail || err?.message || 'Unable to load AI insights right now.';
        this.loading = false;
      },
      complete: () => {
        console.log('IndicatorAssistant: Request completed');
      }
    });
  }

  toggleDetails(): void {
    this.showDetails = !this.showDetails;
  }

  getSentimentScore(): number {
    if (!this.insight) return 50;
    // Use the actual Fear & Greed Index from backend (0-100)
    return this.insight.fear_greed_index ?? 50;
  }

  getSentimentColor(): string {
    if (!this.insight) return '#eab308';
    const score = this.getSentimentScore();
    
    // Color gradient based on score: Red (0-25) -> Orange (25-45) -> Yellow (45-55) -> Light Green (55-75) -> Green (75-100)
    if (score >= 75) return '#22c55e'; // Green - Extreme Greed
    if (score >= 55) return '#84cc16'; // Light Green - Greed
    if (score >= 45) return '#eab308'; // Yellow - Neutral
    if (score >= 25) return '#f97316'; // Orange - Fear
    return '#ef4444'; // Red - Extreme Fear
  }

  getSentimentLabel(): string {
    if (!this.insight) return 'Neutral';
    const score = this.getSentimentScore();
    const sentiment = this.insight.sentiment_label;
    
    // Use score for more accurate labels
    if (score >= 75) return 'Extreme Greed';
    if (score >= 55) return 'Greed';
    if (score >= 45) return 'Neutral';
    if (score >= 25) return 'Fear';
    return 'Extreme Fear';
  }

  getRiskColor(): string {
    if (!this.insight) return '#eab308';
    const risk = this.insight.risk_level;
    if (risk === 'low') return '#22c55e';
    if (risk === 'medium') return '#eab308';
    if (risk === 'elevated') return '#f97316';
    return '#ef4444';
  }

  getGaugePath(): string {
    const score = this.getSentimentScore();
    // Gauge arc: semicircle from left (20, 100) to right (180, 100)
    // Center is at (100, 100), radius is 80
    // Score 0 = left (Fear), Score 50 = top center, Score 100 = right (Greed)
    
    const centerX = 100;
    const centerY = 100;
    const radius = 80;
    
    // Calculate angle: 0-100 maps to 180° to 0° (counterclockwise from left)
    // Score 0 → 180° (left), Score 50 → 90° (top), Score 100 → 0° (right)
    // For SVG arc: we go from left (20, 100) to the end point
    const angle = Math.PI - (score / 100) * Math.PI; // π to 0 radians
    
    // Calculate end point on the arc
    const endX = centerX + radius * Math.cos(angle);
    const endY = centerY - radius * Math.sin(angle);
    
    // Determine if we need large arc (for scores < 50, we need large arc)
    const largeArc = score < 50 ? 1 : 0;
    
    // Arc goes from start (20, 100) to end point, counterclockwise
    return `M 20 100 A 80 80 0 ${largeArc} 0 ${endX} ${endY}`;
  }

  getNeedleTransform(): string {
    const score = this.getSentimentScore();
    // Gauge: semicircle from left (Fear) to right (Greed)
    // Needle line goes from (100, 100) to (100, 20), pointing upward initially
    // In SVG rotate: positive = clockwise, 0° = no rotation
    // We want: Score 0 (Fear) → point left, Score 50 → point up, Score 100 (Greed) → point right
    // The arc goes: left (20, 100) at 180° → top (100, 20) at 90° → right (180, 100) at 0°
    // Needle starts pointing up (toward y=20), which is at 90° on the arc
    // To rotate from up (90°) to left (180°): rotate +90° clockwise
    // To rotate from up (90°) to right (0°): rotate -90° counterclockwise
    // Formula: angle = 90 - (score / 100) * 180
    // Score 0 → 90° (pointing left), Score 50 → 0° (pointing up), Score 100 → -90° (pointing right)
    const angle = 90 - (score / 100) * 180;
    return `rotate(${angle} 100 100)`;
  }

  getNeedleTip(): string {
    // Create a triangle tip for the needle (pointing upward, will be rotated)
    // Points: top center, bottom left, bottom right
    // Adjusted for new coordinate system (center at y=100, top at y=20)
    return '100,20 95,30 105,30';
  }

  getRsi14(): number | null {
    return this.insight?.indicators?.['rsi14'] ?? null;
  }

  getMacd(): number | null {
    const macd = this.insight?.indicators?.['macd'];
    return macd !== null && macd !== undefined ? macd : null;
  }

  getChange24h(): number | null {
    const change = this.insight?.indicators?.['change_percent_24h'];
    return change !== null && change !== undefined ? change : null;
  }

  formatChange24h(): string {
    const change = this.getChange24h();
    if (change === null || change === undefined) return 'N/A';
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  }

  formatAnalysisText(text: string): SafeHtml {
    if (!text) return this.sanitizer.bypassSecurityTrustHtml('');
    
    // Highlight bullish/bearish terms with HTML spans
    let formatted = text
      .replace(/\b(bullish|bull|buy|long|upside|gains|rally|surge|climb|rise|increase|growth|momentum|strength|support|positive|upward|higher)\b/gi, 
        '<span class="bullish-term">$1</span>')
      .replace(/\b(bearish|bear|sell|short|downside|losses|decline|drop|fall|decrease|weakness|resistance|pullback|correction|crash|negative|downward|lower)\b/gi, 
        '<span class="bearish-term">$1</span>')
      .replace(/\b(neutral|hold|sideways|consolidation|range|stable|flat|mixed)\b/gi, 
        '<span class="neutral-term">$1</span>');
    
    return this.sanitizer.bypassSecurityTrustHtml(formatted);
  }

  // Get the displayed price (prefer live price, fallback to insight's last_close)
  getDisplayPrice(): number | null {
    if (this.currentPrice !== null) {
      return this.currentPrice;
    }
    return this.insight?.indicators?.['last_close'] ?? null;
  }

  // Get price source label
  getPriceSource(): string {
    return this.currentPrice !== null ? 'Live' : 'Last Close';
  }
}


