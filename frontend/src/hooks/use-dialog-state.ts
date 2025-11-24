import { useState } from "react";

export default function useDialogState(
  initial = false
): [boolean, (open: boolean) => void] {
  const [open, setOpen] = useState<boolean>(initial);
  return [open, setOpen];
}

