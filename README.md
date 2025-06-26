# SimStack

A Qt-based desktop workflow editor for streamlined computational simulations across multiple scientific disciplines.

## Documentation

For detailed documentation, visit [SimStack Documentation](https://simstack.readthedocs.io/en/latest/)

## Overview

SimStack simplifies complex multiscale workflow creation for materials design, making simulation protocols reusable, reproducible, flexible, and transferable. It bridges physics, materials science, chemistry, and engineering through a client-server architecture connected via SSH.


## Dev Usage

Start the application using :

```bash
pixi run simstack
```
If you have simstackserver as an additional dependency checked out in ../simstackserver you can

```bash
pixi run serverdev
```

with the additional simstackserver runtime dependency.


### Testing
```bash
pixi run tests                    # Run all tests
```


### Building
```bash
pixi run condabuild              # Build conda package
```

## License

MIT License - see [LICENSE](LICENSE) file for details.
