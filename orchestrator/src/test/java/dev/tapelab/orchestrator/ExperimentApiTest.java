package dev.tapelab.orchestrator;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@SpringBootTest
@AutoConfigureMockMvc
class ExperimentApiTest {
    @Autowired MockMvc mvc;

    @Test
    void createsJobsAndReportsStatus() throws Exception {
        String body = """
            {"tickers":["AAPL","MSFT"],"dates":["2025-03-03","2025-03-04"],"configs":["base"]}""";
        mvc.perform(post("/experiments").contentType(MediaType.APPLICATION_JSON).content(body))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.jobs").value(4));
        mvc.perform(get("/experiments/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.PENDING").value(4));
    }

    @Test
    void rejectsEmptyGrid() throws Exception {
        mvc.perform(post("/experiments").contentType(MediaType.APPLICATION_JSON)
                .content("{\"tickers\":[],\"dates\":[],\"configs\":[]}"))
            .andExpect(status().isBadRequest());
    }
}
