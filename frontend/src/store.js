import { configureStore } from "@reduxjs/toolkit";
import hcpsReducer from "./features/hcps/hcpsSlice";
import interactionsReducer from "./features/interactions/interactionsSlice";
import chatReducer from "./features/chat/chatSlice";

export const store = configureStore({
  reducer: {
    hcps: hcpsReducer,
    interactions: interactionsReducer,
    chat: chatReducer,
  },
});
