import { axios } from "axios";
import fs from "fs/promises";
import { execSync } from "child_process";
import moment from "moment";

import { updateStatus } from "./updateStatus";
import { updateConnection } from "./updateConnection"

async function main(){
    await updateConnection("Anonimo93");
    await updateStatus("Online");
}

main();
