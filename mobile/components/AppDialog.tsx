import React from 'react';
import { Dialog, Portal, Text, Button } from 'react-native-paper';

interface DialogAction {
  label: string;
  onPress: () => void;
  mode?: 'text' | 'contained' | 'outlined';
}

interface AppDialogProps {
  visible: boolean;
  title: string;
  message: string;
  onDismiss: () => void;
  actions?: DialogAction[];
}

export function AppDialog({ visible, title, message, onDismiss, actions }: AppDialogProps) {
  const defaultActions: DialogAction[] = actions || [{ label: 'OK', onPress: onDismiss }];
  
  return (
    <Portal>
      <Dialog visible={visible} onDismiss={onDismiss}>
        <Dialog.Title>{title}</Dialog.Title>
        <Dialog.Content>
          <Text>{message}</Text>
        </Dialog.Content>
        <Dialog.Actions>
          {defaultActions.map((action, index) => (
            <Button key={index} onPress={action.onPress} mode={action.mode}>
              {action.label}
            </Button>
          ))}
        </Dialog.Actions>
      </Dialog>
    </Portal>
  );
}
