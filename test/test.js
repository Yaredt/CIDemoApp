var request = require('supertest');
var app = require('../app.js');

describe('GET /', function () {
    it('respond withContinues Integration Demo Application', function (done) {
        request(app).get('/').expect('<!DOCTYPE html> <html><head><title>Continues Integration Demo Application</title><link rel="stylesheet" href="/stylesheets/style.css"></head><body><h1>Continues Integration Demo Application</h1><p>Welcome to Continues Integration Demo Application</p></body></html>', done);
    });
});