const express = require('express');
const app = express();
const PORT = 3000;

app.get('/health', (req, res) => {
  console.log("node health");
  res.send('Node.js Challenge is running!');
});

app.get('/', (req, res) => {
  console.log("hello node");
  res.send('Hello from Node.js Challenge!');
});

app.get('/flag', (req, res) => {
  require('fs').appendFileSync('/tmp/flags', req.query.flag + '\n');
  res.send('Flag submitted');
});

app.listen(PORT, () => {
  console.log(`Node.js Challenge running on port ${PORT}`);
});
