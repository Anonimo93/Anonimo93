import axios from "axios";
import fs from "fs/promises";
import { execSync } from "child_process";
import moment from "moment";

import { updateBotStatus } from "./modules/updateBotStatus.js";
import { updateConnection } from "./modules/updateConnection.js"

async function main(){
    await updateConnection("Anonimo93");
    await updateBotStatus("Online");
}

main();
