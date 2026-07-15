import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import client from "../../api/client";

export const fetchInteractions = createAsyncThunk(
  "interactions/fetchAll",
  async (hcpId) => {
    const { data } = await client.get("/interactions", {
      params: hcpId ? { hcp_id: hcpId } : {},
    });
    return data;
  }
);

export const createInteraction = createAsyncThunk(
  "interactions/create",
  async (payload) => {
    const { data } = await client.post("/interactions", payload);
    return data;
  }
);

export const updateInteraction = createAsyncThunk(
  "interactions/update",
  async ({ id, payload }) => {
    const { data } = await client.patch(`/interactions/${id}`, payload);
    return data;
  }
);

export const deleteInteraction = createAsyncThunk(
  "interactions/delete",
  async (id) => {
    await client.delete(`/interactions/${id}`);
    return id;
  }
);

const interactionsSlice = createSlice({
  name: "interactions",
  initialState: { items: [], status: "idle", error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.items = action.payload;
      })
      .addCase(fetchInteractions.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
      })
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.items.unshift(action.payload);
      })
      .addCase(updateInteraction.fulfilled, (state, action) => {
        const idx = state.items.findIndex((i) => i.id === action.payload.id);
        if (idx !== -1) state.items[idx] = action.payload;
      })
      .addCase(deleteInteraction.fulfilled, (state, action) => {
        state.items = state.items.filter((i) => i.id !== action.payload);
      });
  },
});

export default interactionsSlice.reducer;
