// context/ChatContext.js
import React, { createContext, useContext, useState } from 'react';

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);

  const addMessage = (msg) => {
    setMessages(prev => [...prev, msg]);
  };

  const clearSession = () => {
    setCurrentSession(null);
    setMessages([]);
  };

  const loadSession = (session, msgs) => {
    setCurrentSession(session);
    setMessages(msgs);
  };

  return (
    <ChatContext.Provider value={{
      currentSession, setCurrentSession,
      messages, setMessages, addMessage,
      sessions, setSessions,
      clearSession, loadSession
    }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  return useContext(ChatContext);
}