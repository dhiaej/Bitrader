import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { voiceService } from '../services/voiceService';

interface VoiceCommand {
  transcript: string;
  action: 'buy' | 'sell' | 'cancel' | 'unknown';
  asset?: string;
  amount?: number;
  priceType?: 'market' | 'limit';
  price?: number;
  confidence: number;
}

interface VoiceTradingAssistantProps {
  onTradeCommand: (command: VoiceCommand) => Promise<void>;
}

export const VoiceTradingAssistant: React.FC<VoiceTradingAssistantProps> = ({ onTradeCommand }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [status, setStatus] = useState<'idle' | 'recording' | 'processing' | 'success' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [lastCommand, setLastCommand] = useState<VoiceCommand | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setStatus('recording');
      setError(null);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      setError('Failed to access microphone. Please check permissions.');
      setStatus('error');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
      setStatus('processing');
    }
  };

  const processAudio = async (audioBlob: Blob) => {
    try {
      setIsProcessing(true);
      setStatus('processing');

      // Convert speech to text using Whisper
      const transcriptResult = await voiceService.transcribeAudio(audioBlob);
      setTranscript(transcriptResult);

      // Parse command using llama.cpp
      const command = await voiceService.parseTradeCommand(transcriptResult);
      setLastCommand(command);

      if (command.action === 'unknown' || command.confidence < 0.7) {
        setError('Could not understand the command. Please try again.');
        setStatus('error');
      } else {
        // Execute the trade command
        await onTradeCommand(command);
        setStatus('success');
        
        // Reset after 3 seconds
        setTimeout(() => {
          setStatus('idle');
          setTranscript('');
        }, 3000);
      }
    } catch (err) {
      console.error('Error processing audio:', err);
      setError('Failed to process voice command. Please try again.');
      setStatus('error');
    } finally {
      setIsProcessing(false);
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'recording': return 'bg-red-500';
      case 'processing': return 'bg-yellow-500';
      case 'success': return 'bg-green-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-blue-500';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'recording':
        return <Mic className="w-6 h-6 text-white animate-pulse" />;
      case 'processing':
        return <Loader2 className="w-6 h-6 text-white animate-spin" />;
      case 'success':
        return <CheckCircle className="w-6 h-6 text-white" />;
      case 'error':
        return <XCircle className="w-6 h-6 text-white" />;
      default:
        return <Mic className="w-6 h-6 text-white" />;
    }
  };

  return (
    <div className="voice-trading-assistant p-6 bg-gray-900 rounded-lg shadow-xl border border-gray-800">
      <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
        <Mic className="w-5 h-5" />
        Voice Trading Assistant
      </h3>

      <div className="flex flex-col items-center gap-4">
        {/* Microphone Button */}
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isProcessing}
          className={`relative w-20 h-20 rounded-full ${getStatusColor()} hover:opacity-90 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center shadow-lg hover:shadow-xl transform hover:scale-105 active:scale-95`}
        >
          {getStatusIcon()}
          {isRecording && (
            <span className="absolute -inset-2 rounded-full border-4 border-red-500 animate-ping" />
          )}
        </button>

        {/* Status Text */}
        <div className="text-center">
          {status === 'idle' && (
            <p className="text-gray-400 text-sm">Click to start voice command</p>
          )}
          {status === 'recording' && (
            <p className="text-red-400 text-sm font-medium">Recording... Click to stop</p>
          )}
          {status === 'processing' && (
            <p className="text-yellow-400 text-sm font-medium">Processing your command...</p>
          )}
          {status === 'success' && (
            <p className="text-green-400 text-sm font-medium">Trade command executed!</p>
          )}
          {status === 'error' && (
            <p className="text-red-400 text-sm font-medium">{error}</p>
          )}
        </div>

        {/* Transcript Display */}
        {transcript && (
          <div className="w-full mt-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
            <p className="text-xs text-gray-500 mb-1">Transcript:</p>
            <p className="text-white text-sm">{transcript}</p>
          </div>
        )}

        {/* Parsed Command Display */}
        {lastCommand && lastCommand.action !== 'unknown' && (
          <div className="w-full p-4 bg-gray-800 rounded-lg border border-gray-700">
            <p className="text-xs text-gray-500 mb-2">Parsed Command:</p>
            <div className="space-y-1 text-sm">
              <p className="text-white">
                <span className="text-gray-400">Action:</span>{' '}
                <span className={lastCommand.action === 'buy' ? 'text-green-400' : 'text-red-400'}>
                  {lastCommand.action.toUpperCase()}
                </span>
              </p>
              {lastCommand.asset && (
                <p className="text-white">
                  <span className="text-gray-400">Asset:</span> {lastCommand.asset}
                </p>
              )}
              {lastCommand.amount && (
                <p className="text-white">
                  <span className="text-gray-400">Amount:</span> {lastCommand.amount}
                </p>
              )}
              {lastCommand.priceType && (
                <p className="text-white">
                  <span className="text-gray-400">Type:</span> {lastCommand.priceType.toUpperCase()}
                </p>
              )}
              {lastCommand.price && (
                <p className="text-white">
                  <span className="text-gray-400">Price:</span> ${lastCommand.price}
                </p>
              )}
              <p className="text-white">
                <span className="text-gray-400">Confidence:</span>{' '}
                <span className={lastCommand.confidence > 0.8 ? 'text-green-400' : 'text-yellow-400'}>
                  {(lastCommand.confidence * 100).toFixed(0)}%
                </span>
              </p>
            </div>
          </div>
        )}

        {/* Examples */}
        <div className="w-full mt-4 p-4 bg-gray-800/50 rounded-lg border border-gray-700/50">
          <p className="text-xs text-gray-500 mb-2">Example commands:</p>
          <ul className="text-xs text-gray-400 space-y-1">
            <li>• "Create a sell order for 0.5 BTC at market price"</li>
            <li>• "Buy 2 ETH at market price"</li>
            <li>• "Sell 100 USDT at limit price 0.99"</li>
            <li>• "Cancel all open orders"</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
