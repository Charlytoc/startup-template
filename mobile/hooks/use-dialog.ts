import { useState } from 'react';

interface DialogAction {
  label: string;
  onPress: () => void;
  mode?: 'text' | 'contained' | 'outlined';
}

interface DialogState {
  visible: boolean;
  title: string;
  message: string;
  actions: DialogAction[];
}

export function useDialog() {
  const [state, setState] = useState<DialogState>({
    visible: false,
    title: '',
    message: '',
    actions: []
  });
  
  const show = (title: string, message: string, actions?: DialogAction[]) => {
    setState({ 
      visible: true, 
      title, 
      message, 
      actions: actions || [] 
    });
  };
  
  const hide = () => {
    setState({ 
      visible: false, 
      title: '', 
      message: '', 
      actions: [] 
    });
  };
  
  return { 
    ...state, 
    show, 
    hide 
  };
}
