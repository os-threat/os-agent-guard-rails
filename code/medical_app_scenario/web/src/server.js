require("dotenv").config({ path: "../.env" });
require("dotenv").config();

const app = require("./app");

const port = Number(process.env.API_PORT || process.env.WEB_PORT || 8081);

app.listen(port, () => {
  console.log(`Medical mini-app API listening on http://localhost:${port}`);
});
