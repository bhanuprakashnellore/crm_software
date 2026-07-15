import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import client from "../../api/client";

export const fetchHcps = createAsyncThunk("hcps/fetchAll", async () => {
  const { data } = await client.get("/hcps");
  return data;
});

export const createHcp = createAsyncThunk("hcps/create", async (payload) => {
  const { data } = await client.post("/hcps", payload);
  return data;
});

const hcpsSlice = createSlice({
  name: "hcps",
  initialState: { items: [], status: "idle", error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchHcps.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchHcps.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.items = action.payload;
      })
      .addCase(fetchHcps.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
      })
      .addCase(createHcp.fulfilled, (state, action) => {
        state.items.push(action.payload);
      });
  },
});

export default hcpsSlice.reducer;
