import React from 'react';
import { VoiceTradingAssistant } from '../components/VoiceTradingAssistant';
import { toast } from 'react-hot-toast';

interface VoiceCommand {
  transcript: string;
  action: 'buy' | 'sell' | 'cancel' | 'unknown';
  asset?: string;
  amount?: number;
  priceType?: 'market' | 'limit';
  price?: number;
  confidence: number;
}

/**
 * Example integration of Voice Trading Assistant
 * Add this component to your main trading dashboard
 */
export const VoiceTradingIntegration: React.FC = () => {
  
  // Handle trade command from voice input
  const handleTradeCommand = async (command: VoiceCommand) => {
    try {
      // Show confirmation dialog
      const confirmed = window.confirm(
        `Confirm ${command.action.toUpperCase()} order:\n\n` +
        `Asset: ${command.asset}\n` +
        `Amount: ${command.amount}\n` +
        `Type: ${command.priceType}\n` +
        (command.price ? `Price: $${command.price}\n` : '') +
        `\nConfidence: ${(command.confidence * 100).toFixed(0)}%\n\n` +
        `Do you want to proceed?`
      );

      if (!confirmed) {
        toast.error('Trade cancelled by user');
        return;
      }

      // Execute the trade based on action
      if (command.action === 'cancel') {
        await cancelAllOrders();
      } else {
        await createTradeOrder(command);
      }

      toast.success(`${command.action.toUpperCase()} order created successfully!`);
    } catch (error) {
      console.error('Error executing trade:', error);
      toast.error('Failed to execute trade');
      throw error;
    }
  };

  // Create trade order
  const createTradeOrder = async (command: VoiceCommand) => {
    const orderData = {
      symbol: `${command.asset}USDT`,
      side: command.action,
      type: command.priceType === 'market' ? 'MARKET' : 'LIMIT',
      quantity: command.amount,
      ...(command.price && { price: command.price }),
    };

    // TODO: Replace with your actual trading API call
    const response = await fetch('/api/orders/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(orderData),
    });

    if (!response.ok) {
      throw new Error('Failed to create order');
    }

    return response.json();
  };

  // Cancel all orders
  const cancelAllOrders = async () => {
    // TODO: Replace with your actual cancel orders API call
    const response = await fetch('/api/orders/cancel-all', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error('Failed to cancel orders');
    }

    return response.json();
  };

  return (
    <div className="voice-trading-integration">
      <VoiceTradingAssistant onTradeCommand={handleTradeCommand} />
    </div>
  );
};
