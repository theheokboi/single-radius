const sleep = s => new Promise(r => setTimeout(r, s*1000));
const axios = require("axios")

class MeasurementPool {

    constructor(apiKey, ttl=600) {
        this.apiKey = apiKey
        this.ttl = ttl
        this.activeMeasurementCount = 0
        this.cleanupMeasurementsTimer = null
        this.cacheCapacity = 100
        this.cleanUpMeasurementsInterval = 120 * 1000 // 120 seconds
        this.ripeEndpoint = "https://atlas.ripe.net/api/v2/measurements/"
        this.keyString = "?key=" + this.apiKey
        this.measurementMap = new Map()
        this.stoppedStatuses = new Set(['Stopped', 'Forced to stop', 'No suitable probes', 'Failed or Archived'])
    }

    run() { this.setup()}
    async setup() {
        this.cleanupMeasurementsTimer = setInterval(() => {this.cleanUpMeasurements() },
        this.cleanUpMeasurementsInterval
       )
       console.log("MeasurementPool started with cleanupMeasurementsInterval " + this.cleanUpMeasurementsInterval)
    }

    async kickoffMeasurement(targetAddress, probes, mType="ping") {
        while (this.measurementMap.size >= this.cacheCapacity) {
            console.log("Cache exceeded capacity, sleeping 10 seconds")
            await sleep(20)
        }
        let definitions = [
            {
                "target" : "ripe.net",
                "description" : "pinging",
                "af" : 4,
                "type" : "ping",
            }   
        ]

        let p = [
            {
                "type" : "probe",
                "value" : probes,
                "requested" : probes.length
            }
        ]

        let form = {
            "definitions": [
              {
                "target": targetAddress,
                "description": `Pinging ${targetAddress}`,
                "type": "ping",
                "af": 4
              }
            ],
            "probes": [
              {
                "action" : "add",
                "requested": probes.length,
                "type": "probes",
                "value": probes.join(",")
              }
            ]
          }
    
        console.log(form)

        let finalUrl = this.ripeEndpoint + this.keyString
        console.log(finalUrl)
        axios.post(finalUrl, form)
        .then( (response) => {
            let measurementId = response.data.measurements[0]
            this.measurementMap.set(measurementId, Date.now())
            console.log(`Added measurement with id ${measurementId} into measurementSet`)
        })
        .catch((error) => console.log(error.response.data.error.errors)) //hoping the error is from the http request, not the js code

    }

    async cleanUpMeasurement(id) {
        let finalUrl = this.ripeEndpoint.concat(id, this.keyString)
        console.log(finalUrl)
        axios.get(finalUrl)
        .then((response) => {
            if (this.stoppedStatuses.has(response.data.status.name)) {
                this.measurementMap.delete(id)
                console.log(`Removed measurement with id ${id} from measurementSet`)
            } else {
                console.log(`Measurement with ${id} has status ${response.data.status.name}`)
            }
        })
        .catch((error) => console.log(error))
    }
    async cleanUpMeasurements() {
        this.measurementMap.forEach( (creationTime, id) => {
            if (Date.now() - creationTime > ttl * 1000) {
                this.measurementMap.delete(id)
            } else {
                this.cleanUpMeasurement(id)
            }
            
        })
    }
}


if (require.main === module) {
    var pool = new MeasurementPool('380531a9-c3fb-424f-8d1b-23cda9b881fd')
    pool.run()
    pool.measurementMap.set("50166060", Date.now())
    pool.cleanUpMeasurement("50166060")
    //pool.kickoffMeasurement("128.128.128.1", [100])
}
