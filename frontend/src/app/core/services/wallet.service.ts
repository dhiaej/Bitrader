import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { ApiService } from './api.service';

export interface Wallet {
  id: number;
  user_id: number;
  currency: string;
  available_balance: string;
  locked_balance: string;
  created_at: string;
}

export interface Transaction {
  id: number;
  wallet_id: number;
  type: string;
  amount: string;
  currency: string;
  status: string;
  description: string;
  created_at: string;
}

export interface TransferRequest {
  recipient_username: string;
  currency: string;
  amount: number;
}

@Injectable({
  providedIn: 'root'
})
export class WalletService {
  private walletsSubject = new BehaviorSubject<Wallet[]>([]);
  public wallets$ = this.walletsSubject.asObservable();

  private transactionsSubject = new BehaviorSubject<Transaction[]>([]);
  public transactions$ = this.transactionsSubject.asObservable();

  constructor(private api: ApiService) {}

  loadWallets(): void {
    this.api.get<Wallet[]>('/wallet/balances').subscribe({
      next: (wallets) => this.walletsSubject.next(wallets),
      error: (error) => console.error('Error loading wallets:', error)
    });
  }

  getWallets(): Observable<Wallet[]> {
    return this.api.get<Wallet[]>('/wallet/balances').pipe(
      tap(wallets => this.walletsSubject.next(wallets))
    );
  }

  getWallet(currency: string): Wallet | undefined {
    return this.walletsSubject.value.find(w => w.currency === currency);
  }

  deposit(currency: string, amount: number): Observable<Transaction> {
    return this.api.post<Transaction>('/wallet/deposit', {
      currency,
      amount
    }).pipe(
      tap(() => this.loadWallets())
    );
  }

  withdraw(currency: string, amount: number, address: string): Observable<Transaction> {
    return this.api.post<Transaction>('/wallet/withdraw', {
      currency,
      amount,
      address
    }).pipe(
      tap(() => this.loadWallets())
    );
  }

  transfer(data: TransferRequest): Observable<any> {
    return this.api.post('/wallet/transfer', data).pipe(
      tap(() => this.loadWallets())
    );
  }

  getTransactionHistory(): Observable<Transaction[]> {
    return this.api.get<Transaction[]>('/wallet/transactions').pipe(
      tap(transactions => this.transactionsSubject.next(transactions))
    );
  }

  getTotalBalanceUSD(): number {
    // Simple calculation - in real app would use live prices
    const wallets = this.walletsSubject.value;
    let total = 0;

    wallets.forEach(wallet => {
      const balance = parseFloat(wallet.available_balance);
      switch(wallet.currency) {
        case 'USD':
        case 'USDT':
          total += balance;
          break;
        case 'BTC':
          total += balance * 45000; // Mock price
          break;
        case 'ETH':
          total += balance * 3000; // Mock price
          break;
      }
    });

    return total;
  }
}
