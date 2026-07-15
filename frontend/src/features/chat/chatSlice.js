import { createSlice, createAsyncThunk, nanoid } from "@reduxjs/toolkit";
import client from "../../api/client";

export const sendChatMessage = createAsyncThunk(
  "chat/send",
  async ({ message, threadId }) => {
    const { data } = await client.post("/chat", {
      message,
      thread_id: threadId,
    });
    return data;
  }
);

const chatSlice = createSlice({
  name: "chat",
  initialState: {
    threadId: nanoid(),
    messages: [], // { role: 'user' | 'assistant', text, toolCalls? }
    status: "idle",
    error: null,
  },
  reducers: {
    resetConversation: (state) => {
      state.threadId = nanoid();
      state.messages = [];
      state.status = "idle";
      state.error = null;
    },
    addUserMessage: (state, action) => {
      state.messages.push({ role: "user", text: action.payload });
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state) => {
        state.status = "loading";
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.messages.push({
          role: "assistant",
          text: action.payload.reply,
          toolCalls: action.payload.tool_calls,
        });
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
        state.messages.push({
          role: "assistant",
          text: "Sorry, something went wrong reaching the agent.",
          toolCalls: [],
        });
      });
  },
});

export const { resetConversation, addUserMessage } = chatSlice.actions;
export default chatSlice.reducer;
