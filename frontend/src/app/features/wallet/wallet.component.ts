import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { WalletService, Wallet, Transaction } from '../../core/services/wallet.service';

@Component({
  selector: 'app-wallet',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './wallet.component.html',
  styleUrls: ['./wallet.component.scss']
})
export class WalletComponent implements OnInit {
  wallets: Wallet[] = [];
  transactions: Transaction[] = [];
  depositForm: FormGroup;
  withdrawForm: FormGroup;
  transferForm: FormGroup;
  showDepositModal = false;
  showWithdrawModal = false;
  showTransferModal = false;
  selectedWallet: Wallet | null = null;
  isLoading = false;
  errorMessage = '';
  successMessage = '';

  constructor(
    private fb: FormBuilder,
    private walletService: WalletService
  ) {
    this.depositForm = this.fb.group({
      amount: ['', [Validators.required, Validators.min(0.01)]]
    });

    this.withdrawForm = this.fb.group({
      amount: ['', [Validators.required, Validators.min(0.01)]],
      address: ['']  // Optional for virtual game
    });

    this.transferForm = this.fb.group({
      recipient_username: ['', [Validators.required]],
      amount: ['', [Validators.required, Validators.min(0.01)]]
    });
  }

  ngOnInit(): void {
    this.loadWallets();
    this.loadTransactions();
  }

  loadWallets(): void {
    this.walletService.getWallets().subscribe({
      next: (wallets) => {
        this.wallets = wallets;
      },
      error: (error) => console.error('Error loading wallets:', error)
    });
  }

  loadTransactions(): void {
    this.walletService.getTransactionHistory().subscribe({
      next: (transactions) => {
        this.transactions = transactions;
      },
      error: (error) => console.error('Error loading transactions:', error)
    });
  }

  openDepositModal(wallet: Wallet): void {
    this.selectedWallet = wallet;
    this.showDepositModal = true;
    this.depositForm.reset();
  }

  openWithdrawModal(wallet: Wallet): void {
    this.selectedWallet = wallet;
    this.showWithdrawModal = true;
    this.withdrawForm.reset();
  }

  openTransferModal(wallet: Wallet): void {
    this.selectedWallet = wallet;
    this.showTransferModal = true;
    this.transferForm.reset();
  }

  closeModals(): void {
    this.showDepositModal = false;
    this.showWithdrawModal = false;
    this.showTransferModal = false;
    this.selectedWallet = null;
    this.errorMessage = '';
  }

  onDeposit(): void {
    if (!this.selectedWallet || this.depositForm.invalid) return;

    this.isLoading = true;
    this.errorMessage = '';

    this.walletService.deposit(
      this.selectedWallet.currency,
      this.depositForm.value.amount
    ).subscribe({
      next: () => {
        this.isLoading = false;
        this.successMessage = 'Deposit successful!';
        this.closeModals();
        this.loadWallets();
        this.loadTransactions();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Deposit error:', error);
        this.errorMessage = error.error?.detail || error.message || 'Deposit failed';
      }
    });
  }

  onWithdraw(): void {
    if (!this.selectedWallet || this.withdrawForm.invalid) return;

    this.isLoading = true;
    this.errorMessage = '';

    this.walletService.withdraw(
      this.selectedWallet.currency,
      this.withdrawForm.value.amount,
      this.withdrawForm.value.address
    ).subscribe({
      next: () => {
        this.isLoading = false;
        this.successMessage = 'Withdrawal successful!';
        this.closeModals();
        this.loadWallets();
        this.loadTransactions();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Withdraw error:', error);
        this.errorMessage = error.error?.detail || error.message || 'Withdrawal failed';
      }
    });
  }

  onTransfer(): void {
    if (!this.selectedWallet || this.transferForm.invalid) return;

    this.isLoading = true;
    this.errorMessage = '';

    const transferData = {
      ...this.transferForm.value,
      currency: this.selectedWallet.currency
    };

    this.walletService.transfer(transferData).subscribe({
      next: () => {
        this.isLoading = false;
        this.successMessage = 'Transfer successful!';
        this.closeModals();
        this.loadWallets();
        this.loadTransactions();
        setTimeout(() => this.successMessage = '', 3000);
      },
      error: (error) => {
        this.isLoading = false;
        this.errorMessage = error.error?.detail || 'Transfer failed';
      }
    });
  }

  formatBalance(balance: string): string {
    return parseFloat(balance).toFixed(8);
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleString();
  }

  getTotalBalance(): number {
    return this.walletService.getTotalBalanceUSD();
  }

  getTransactionIcon(type: string): string {
    const icons: {[key: string]: string} = {
      'DEPOSIT': 'deposit',
      'WITHDRAWAL': 'up',
      'TRANSFER_OUT': 'right',
      'TRANSFER_IN': 'left',
      'TRADE_BUY': 'cart',
      'TRADE_SELL': 'wallet',
      'ESCROW_LOCK': 'lock',
      'ESCROW_RELEASE': 'unlock'
    };
    return icons[type] || 'note';
  }
}
